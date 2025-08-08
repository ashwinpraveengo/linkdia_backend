from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.http import HttpRequest

User = get_user_model()


class GraphQLAuthenticationMiddleware:
    """
    Custom middleware to add JWT authentication support to GraphQL requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request
        self.process_request(request)
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Add authenticated user to request for GraphQL
        """
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            # Try to authenticate using JWT
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                try:
                    # Use Django REST Framework's JWT authentication
                    jwt_auth = JWTAuthentication()
                    
                    # Create a fake request with the token
                    fake_request = HttpRequest()
                    fake_request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
                    
                    # Authenticate
                    auth_result = jwt_auth.authenticate(fake_request)
                    
                    if auth_result:
                        user, validated_token = auth_result
                        request.user = user
                    else:
                        request.user = AnonymousUser()
                        
                except (InvalidToken, Exception):
                    request.user = AnonymousUser()
            else:
                request.user = AnonymousUser()


def get_graphql_context(request):
    """
    Custom context function for GraphQL that ensures proper authentication
    """
    # Ensure user is set on request
    if not hasattr(request, 'user'):
        request.user = AnonymousUser()
    
    return request
