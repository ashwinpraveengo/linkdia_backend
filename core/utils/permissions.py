from typing import Optional
from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError
from core.models import (
    CustomUser,
    ProfessionalProfile,
    ClientProfile,
    ProfessionalDocument,
    VideoKYC,
    Portfolio,
)
from core.utils.decorators import require_professional

# Alias for better naming
professional_required = require_professional

# Another alias for GraphQL mutations  
require_professional_user = require_professional


def can_view_profile(user: CustomUser, target_profile: ProfessionalProfile) -> bool:
    """
    Check if user can view a professional's profile
    
    Args:
        user: User requesting access
        target_profile: Professional profile to view
    
    Returns:
        bool: True if user can view the profile
    """
    if not user or isinstance(user, AnonymousUser):
        # Anonymous users can only view verified profiles
        return target_profile.verification_status == 'VERIFIED'
    
    # Users can always view their own profile
    if user == target_profile.user:
        return True
    
    # Verified professionals can view each other's profiles
    if (user.is_professional and
        hasattr(user, 'professional_profile') and
        user.professional_profile.verification_status == 'VERIFIED'):
        return True
    
    # Clients can view verified professional profiles
    if user.is_client and target_profile.verification_status == 'VERIFIED':
        return True
    
    return False


def can_edit_profile(user: CustomUser, target_profile: ProfessionalProfile) -> bool:
    """
    Check if user can edit a professional's profile
    
    Args:
        user: User requesting access
        target_profile: Professional profile to edit
    
    Returns:
        bool: True if user can edit the profile
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    # Users can only edit their own profile
    return user == target_profile.user


def can_view_documents(user: CustomUser, document: ProfessionalDocument) -> bool:
    """
    Check if user can view a professional's documents
    
    Args:
        user: User requesting access
        document: Document to view
    
    Returns:
        bool: True if user can view the document
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    # Document owner can always view
    if user == document.professional.user:
        return True
    
    # Admin users (is_staff) can view for verification purposes
    if user.is_staff:
        return True
    
    # Other users cannot view private documents
    return False


def can_verify_kyc(user: CustomUser, kyc_session: VideoKYC) -> bool:
    """
    Check if user can verify a KYC session
    
    Args:
        user: User requesting to verify
        kyc_session: KYC session to verify
    
    Returns:
        bool: True if user can verify
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    # Only admin/staff users can verify KYC
    if not user.is_staff:
        return False
    
    # KYC must be completed to be verifiable
    return kyc_session.status == 'COMPLETED'


def is_profile_owner(user: CustomUser, profile_id: str, profile_type: str = 'professional') -> bool:
    """
    Check if user owns a specific profile
    
    Args:
        user: User to check
        profile_id: ID of the profile
        profile_type: Type of profile ('professional' or 'client')
    
    Returns:
        bool: True if user owns the profile
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    try:
        if profile_type == 'professional':
            profile = ProfessionalProfile.objects.get(id=profile_id)
            return user == profile.user
        elif profile_type == 'client':
            profile = ClientProfile.objects.get(id=profile_id)
            return user == profile.user
    except (ProfessionalProfile.DoesNotExist, ClientProfile.DoesNotExist):
        return False
    
    return False


def can_manage_availability(user: CustomUser, professional_profile: ProfessionalProfile) -> bool:
    """
    Check if user can manage availability for a professional
    
    Args:
        user: User requesting to manage availability
        professional_profile: Professional profile
    
    Returns:
        bool: True if user can manage availability
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    # Only the profile owner can manage their availability
    return user == professional_profile.user and user.is_professional


def can_access_portfolio(user: CustomUser, portfolio: Portfolio) -> bool:
    """
    Check if user can access a portfolio
    
    Args:
        user: User requesting access
        portfolio: Portfolio to access
    
    Returns:
        bool: True if user can access portfolio
    """
    # Portfolios are publicly viewable for now (simplified)
    if not user or isinstance(user, AnonymousUser):
        return True
    
    # Portfolio owner can always access
    if user == portfolio.professional.user:
        return True
    
    # Admin users can access for verification
    if user.is_staff:
        return True
    
    return True


def require_permission(permission_func, *permission_args, error_message: str = "Permission denied"):
    """
    Decorator to require specific permissions for GraphQL resolvers
    
    Args:
        permission_func: Permission check function
        *permission_args: Arguments to pass to permission function (excluding user)
        error_message: Error message to show if permission denied
    """
    def decorator(func):
        def wrapper(self, info, *args, **kwargs):
            user = info.context.user
            
            # Call permission function with user as first argument
            if not permission_func(user, *permission_args):
                raise GraphQLError(error_message)
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator
