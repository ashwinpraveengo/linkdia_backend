"""
GraphQL queries for file retrieval
"""
import graphene
from graphene import ObjectType, Field, String, ID, List
from django.contrib.auth import get_user_model
from django.http import Http404

from core.models import (
    ProfessionalDocument,
    Portfolio,
)
from core.types.file_types import FileInfoType, FileDownloadType
from core.utils.file_handlers import FileStorageHandler
from core.utils.decorators import login_required

User = get_user_model()


class FileQuery(ObjectType):
    """File-related queries"""
    
    # Get file information without downloading
    profile_picture_info = Field(FileInfoType, user_id=ID())
    document_info = Field(FileInfoType, document_id=ID(required=True))
    portfolio_document_info = Field(FileInfoType, portfolio_id=ID(required=True))
    
    # Get download information
    download_document = Field(FileDownloadType, document_id=ID(required=True))
    download_portfolio_document = Field(FileDownloadType, portfolio_id=ID(required=True))
    download_profile_picture = Field(FileDownloadType, user_id=ID())
    
    def resolve_profile_picture_info(self, info, user_id=None):
        """Get profile picture information"""
        try:
            if user_id:
                # Admin or specific user lookup
                if not info.context.user.is_staff and str(info.context.user.id) != user_id:
                    raise PermissionError("Not authorized to access this profile picture")
                user = User.objects.get(id=user_id)
            else:
                # Current user
                if not info.context.user.is_authenticated:
                    return None
                user = info.context.user
            
            return FileInfoType.from_instance(user, 'profile_picture')
            
        except User.DoesNotExist:
            return None
        except PermissionError:
            return None
    
    @login_required
    def resolve_document_info(self, info, document_id):
        """Get professional document information"""
        try:
            user = info.context.user
            
            # Only professional can access their own documents, or staff
            if user.is_staff:
                document = ProfessionalDocument.objects.get(id=document_id)
            else:
                document = ProfessionalDocument.objects.get(
                    id=document_id,
                    professional__user=user
                )
            
            return FileInfoType.from_instance(document, 'document')
            
        except ProfessionalDocument.DoesNotExist:
            return None
    
    @login_required
    def resolve_portfolio_document_info(self, info, portfolio_id):
        """Get portfolio document information"""
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            
            # Check if user can access this portfolio
            if not info.context.user.is_staff:
                if (portfolio.professional.user != info.context.user and 
                    portfolio.status != 'PUBLISHED'):
                    return None
            
            return FileInfoType.from_instance(portfolio, 'portfolio_document')
            
        except Portfolio.DoesNotExist:
            return None
    
    def resolve_download_profile_picture(self, info, user_id=None):
        """Get profile picture download info"""
        try:
            if user_id:
                if not info.context.user.is_staff and str(info.context.user.id) != user_id:
                    return None
                user = User.objects.get(id=user_id)
            else:
                if not info.context.user.is_authenticated:
                    return None
                user = info.context.user
            
            file_info = FileStorageHandler.get_file_info(user, 'profile_picture')
            if not file_info:
                return None
            
            return FileDownloadType(
                download_url=f"/api/files/profile-picture/{user.id}/",
                filename=file_info['name'],
                content_type=file_info['content_type'],
                size=file_info['size']
            )
            
        except User.DoesNotExist:
            return None
    
    @login_required
    def resolve_download_document(self, info, document_id):
        """Get document download info"""
        try:
            user = info.context.user
            
            if user.is_staff:
                document = ProfessionalDocument.objects.get(id=document_id)
            else:
                document = ProfessionalDocument.objects.get(
                    id=document_id,
                    professional__user=user
                )
            
            file_info = FileStorageHandler.get_file_info(document, 'document')
            if not file_info:
                return None
            
            return FileDownloadType(
                download_url=f"/api/files/document/{document.id}/",
                filename=file_info['name'],
                content_type=file_info['content_type'],
                size=file_info['size']
            )
            
        except ProfessionalDocument.DoesNotExist:
            return None
    
    @login_required
    def resolve_download_portfolio_document(self, info, portfolio_id):
        """Get portfolio document download info"""
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            
            if not info.context.user.is_staff:
                if (portfolio.professional.user != info.context.user and 
                    portfolio.status != 'PUBLISHED'):
                    return None
            
            file_info = FileStorageHandler.get_file_info(portfolio, 'portfolio_document')
            if not file_info:
                return None
            
            return FileDownloadType(
                download_url=f"/api/files/portfolio-document/{portfolio.id}/",
                filename=file_info['name'],
                content_type=file_info['content_type'],
                size=file_info['size']
            )
            
        except Portfolio.DoesNotExist:
            return None
