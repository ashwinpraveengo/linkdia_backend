"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from core.middleware import get_graphql_context

class CustomFileUploadGraphQLView(FileUploadGraphQLView):
    """
    Custom GraphQL view that handles file uploads and authentication context
    """
    
    def get_context(self, request):
        """
        Return the GraphQL context with authenticated user
        """
        return get_graphql_context(request)

def home_view(request):
    """Simple home view for the API root"""
    return JsonResponse({
        'message': 'Welcome to LinkDia API',
        'endpoints': {
            'graphql': '/graphql/',
            'admin': '/admin/',
            'accounts': '/accounts/'
        }
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(
        CustomFileUploadGraphQLView.as_view(
            graphiql=True
        )
    )),
    path('accounts/', include('allauth.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
