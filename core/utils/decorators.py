import functools
import time
from typing import Dict, Any, Callable
from django.core.cache import cache
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError
from core.models import CustomUser, ProfessionalProfile
import logging

logger = logging.getLogger(__name__)


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require user authentication for GraphQL resolvers
    """
    @functools.wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = info.context.user
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise GraphQLError("Authentication required")
        return func(self, info, *args, **kwargs)
    return wrapper


# Alias for better naming consistency
login_required = require_authentication


def require_professional(func: Callable) -> Callable:
    """
    Decorator to require professional user type
    """
    @functools.wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = info.context.user
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        if not user.is_professional:
            raise GraphQLError("Professional account required")
        
        return func(self, info, *args, **kwargs)
    return wrapper


def require_client(func: Callable) -> Callable:
    """
    Decorator to require client user type
    """
    @functools.wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = info.context.user
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        if not user.is_client:
            raise GraphQLError("Client account required")
        
        return func(self, info, *args, **kwargs)
    return wrapper


def require_verification(verification_status: str = 'VERIFIED') -> Callable:
    """
    Decorator to require professional verification status
    
    Args:
        verification_status: Required verification status
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            user = info.context.user
            if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
                raise GraphQLError("Authentication required")
            
            if not user.is_professional:
                raise GraphQLError("Professional account required")
            
            try:
                profile = user.professional_profile
                if profile.verification_status != verification_status:
                    raise GraphQLError(f"Professional verification status '{verification_status}' required")
            except ProfessionalProfile.DoesNotExist:
                raise GraphQLError("Professional profile not found")
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(
    key_prefix: str,
    max_requests: int = 100,
    time_window: int = 3600,  # 1 hour in seconds
    per_user: bool = True
) -> Callable:
    """
    Decorator to implement rate limiting for GraphQL mutations
    
    Args:
        key_prefix: Prefix for cache key
        max_requests: Maximum requests allowed in time window
        time_window: Time window in seconds
        per_user: Whether to rate limit per user or globally
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            if per_user:
                user = info.context.user
                if user and user.is_authenticated:
                    cache_key = f"rate_limit:{key_prefix}:user:{user.id}"
                else:
                    # Use IP address for anonymous users
                    ip_address = info.context.META.get('REMOTE_ADDR', 'unknown')
                    cache_key = f"rate_limit:{key_prefix}:ip:{ip_address}"
            else:
                cache_key = f"rate_limit:{key_prefix}:global"
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= max_requests:
                raise GraphQLError(f"Rate limit exceeded. Try again later.")
            
            # Increment count
            cache.set(cache_key, current_count + 1, time_window)
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


def log_mutation(operation_name: str = None) -> Callable:
    """
    Decorator to log GraphQL mutations
    
    Args:
        operation_name: Name of the operation (optional)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            start_time = time.time()
            
            # Get operation info
            operation = operation_name or func.__name__
            user = info.context.user
            user_id = user.id if user and user.is_authenticated else None
            
            # Log mutation start
            logger.info(f"Mutation started: {operation}, User: {user_id}")
            
            try:
                result = func(self, info, *args, **kwargs)
                
                # Log successful completion
                execution_time = time.time() - start_time
                logger.info(f"Mutation completed: {operation}, User: {user_id}, Time: {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                # Log error
                execution_time = time.time() - start_time
                logger.error(f"Mutation failed: {operation}, User: {user_id}, Time: {execution_time:.2f}s, Error: {str(e)}")
                raise
        
        return wrapper
    return decorator


def validate_input(**validators) -> Callable:
    """
    Decorator to validate input parameters
    
    Args:
        **validators: Dictionary of field names and validator functions
    
    Example:
        @validate_input(
            email=lambda x: validate_email_format(x),
            phone=lambda x: validate_phone_number(x)['is_valid']
        )
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            errors = []
            
            for field_name, validator in validators.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    try:
                        is_valid = validator(value)
                        if not is_valid:
                            errors.append(f"Invalid {field_name}")
                    except Exception as e:
                        errors.append(f"Validation error for {field_name}: {str(e)}")
            
            if errors:
                raise GraphQLError(f"Validation failed: {', '.join(errors)}")
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


def cache_result(
    cache_key_template: str,
    timeout: int = 300,  # 5 minutes
    vary_on_user: bool = False
) -> Callable:
    """
    Decorator to cache GraphQL query results
    
    Args:
        cache_key_template: Template for cache key (can use {user_id}, {args}, etc.)
        timeout: Cache timeout in seconds
        vary_on_user: Whether to include user ID in cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            # Build cache key
            cache_key_vars = {
                'function_name': func.__name__,
                'args': str(args),
                'kwargs': str(sorted(kwargs.items()))
            }
            
            if vary_on_user:
                user = info.context.user
                cache_key_vars['user_id'] = user.id if user and user.is_authenticated else 'anonymous'
            
            cache_key = cache_key_template.format(**cache_key_vars)
            
            # Try to get cached result
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(self, info, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def handle_exceptions(
    default_message: str = "An error occurred",
    log_errors: bool = True
) -> Callable:
    """
    Decorator to handle exceptions in GraphQL resolvers
    
    Args:
        default_message: Default error message to show users
        log_errors: Whether to log errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            try:
                return func(self, info, *args, **kwargs)
            except GraphQLError:
                # Re-raise GraphQL errors as-is
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                
                # Return user-friendly error
                raise GraphQLError(default_message)
        return wrapper
    return decorator


def require_fields(*required_fields) -> Callable:
    """
    Decorator to require specific fields in input
    
    Args:
        *required_fields: Field names that are required
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, info, *args, **kwargs):
            missing_fields = []
            
            for field in required_fields:
                if field not in kwargs or kwargs[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                raise GraphQLError(f"Required fields missing: {', '.join(missing_fields)}")
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator


def transaction_atomic(func: Callable) -> Callable:
    """
    Decorator to wrap GraphQL mutations in database transactions
    """
    from django.db import transaction
    
    @functools.wraps(func)
    def wrapper(self, info, *args, **kwargs):
        with transaction.atomic():
            return func(self, info, *args, **kwargs)
    return wrapper
