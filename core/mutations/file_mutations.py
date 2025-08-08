"""
GraphQL mutations for file uploads using binary storage
"""
import graphene
from graphene import ObjectType, Mutation, String, Boolean, Field, ID
from graphene_file_upload.scalars import Upload
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404

from core.models import (
    ProfessionalProfile,
    ProfessionalDocument, 
    Portfolio,
)
from core.types.user import UserType
from core.types.proffesional_profile import (
    ProfessionalDocumentType,
    PortfolioType,
)
from core.types.file_types import FileUploadResponse, FileInfoType
from core.utils.file_handlers import FileUploadMixin
from core.utils.decorators import login_required
from core.utils.permissions import require_professional_user

User = get_user_model()


class UpdateProfilePictureMutation(Mutation, FileUploadMixin):
    """Upload or update user profile picture"""
    
    class Arguments:
        profile_picture = Upload(required=True)
    
    success = Boolean()
    message = String()
    user = Field(UserType)
    errors = graphene.List(String)
    
    @staticmethod
    @login_required
    def mutate(root, info, profile_picture):
        try:
            user = info.context.user
            
            # Handle file upload
            mutation = UpdateProfilePictureMutation()
            mutation.handle_file_upload(
                profile_picture, 
                'profile_picture', 
                user, 
                file_type='image',
                max_size_key='profile_picture'
            )
            
            user.save()
            
            return UpdateProfilePictureMutation(
                success=True,
                message="Profile picture updated successfully",
                user=user
            )
            
        except ValidationError as e:
            return UpdateProfilePictureMutation(
                success=False,
                message="Validation error",
                errors=e.messages if hasattr(e, 'messages') else [str(e)]
            )
        except Exception as e:
            return UpdateProfilePictureMutation(
                success=False,
                message="An error occurred while uploading the profile picture",
                errors=[str(e)]
            )


class RemoveProfilePictureMutation(Mutation, FileUploadMixin):
    """Remove user profile picture"""
    
    success = Boolean()
    message = String()
    user = Field(UserType)
    
    @staticmethod
    @login_required
    def mutate(root, info):
        try:
            user = info.context.user
            
            # Clear file fields
            mutation = RemoveProfilePictureMutation()
            mutation.clear_file_fields(user, 'profile_picture')
            
            user.save()
            
            return RemoveProfilePictureMutation(
                success=True,
                message="Profile picture removed successfully",
                user=user
            )
            
        except Exception as e:
            return RemoveProfilePictureMutation(
                success=False,
                message="An error occurred while removing the profile picture"
            )


class UploadProfessionalDocumentMutation(Mutation, FileUploadMixin):
    """Upload a professional document"""
    
    class Arguments:
        document_type = String(required=True)
        document_file = Upload(required=True)
        document_number = String(required=False)
        issued_date = graphene.Date(required=False)
        expiry_date = graphene.Date(required=False)
        issuing_authority = String(required=False)
    
    success = Boolean()
    message = String()
    document = Field(ProfessionalDocumentType)
    errors = graphene.List(String)
    
    @staticmethod
    @login_required
    @require_professional_user
    def mutate(root, info, document_type, document_file, **kwargs):
        try:
            user = info.context.user
            professional_profile = user.professional_profile
            
            # Check if document type already exists
            existing_doc = ProfessionalDocument.objects.filter(
                professional=professional_profile,
                document_type=document_type
            ).first()
            
            if existing_doc:
                # Update existing document
                document = existing_doc
            else:
                # Create new document
                document = ProfessionalDocument(
                    professional=professional_profile,
                    document_type=document_type
                )
            
            # Handle file upload
            mutation = UploadProfessionalDocumentMutation()
            mutation.handle_file_upload(
                document_file, 
                'document', 
                document, 
                file_type='document',
                max_size_key='document'
            )
            
            # Update other fields
            document.document_number = kwargs.get('document_number', '')
            document.issued_date = kwargs.get('issued_date')
            document.expiry_date = kwargs.get('expiry_date')
            document.issuing_authority = kwargs.get('issuing_authority', '')
            document.verification_status = 'PENDING'
            document.original_filename = document.document_name
            
            document.save()
            
            # Update onboarding progress
            if hasattr(professional_profile, 'onboarding_progress'):
                progress = professional_profile.onboarding_progress
                progress.total_documents_uploaded = professional_profile.documents.count()
                
                if progress.total_documents_uploaded >= progress.minimum_documents_required:
                    progress.mark_step_completed('DOCUMENTS_UPLOADED')
                
                progress.save()
            
            return UploadProfessionalDocumentMutation(
                success=True,
                message="Document uploaded successfully",
                document=document
            )
            
        except ValidationError as e:
            return UploadProfessionalDocumentMutation(
                success=False,
                message="Validation error",
                errors=e.messages if hasattr(e, 'messages') else [str(e)]
            )
        except Exception as e:
            return UploadProfessionalDocumentMutation(
                success=False,
                message="An error occurred while uploading the document",
                errors=[str(e)]
            )


class DeleteProfessionalDocumentMutation(Mutation):
    """Delete a professional document"""
    
    class Arguments:
        document_id = ID(required=True)
    
    success = Boolean()
    message = String()
    errors = graphene.List(String)
    
    @staticmethod
    @login_required
    @require_professional_user
    def mutate(root, info, document_id):
        try:
            user = info.context.user
            professional_profile = user.professional_profile
            
            try:
                document = ProfessionalDocument.objects.get(
                    id=document_id,
                    professional=professional_profile
                )
            except ProfessionalDocument.DoesNotExist:
                raise Http404("Document not found")
            
            document.delete()
            
            # Update onboarding progress
            if hasattr(professional_profile, 'onboarding_progress'):
                progress = professional_profile.onboarding_progress
                progress.total_documents_uploaded = professional_profile.documents.count()
                progress.save()
            
            return DeleteProfessionalDocumentMutation(
                success=True,
                message="Document deleted successfully"
            )
            
        except Http404 as e:
            return DeleteProfessionalDocumentMutation(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            return DeleteProfessionalDocumentMutation(
                success=False,
                message="An error occurred while deleting the document",
                errors=[str(e)]
            )


class UpdatePortfolioMutation(Mutation, FileUploadMixin):
    """Update portfolio with optional file uploads"""
    
    class Arguments:
        portfolio_id = ID(required=False)  # If not provided, creates new portfolio
        title = String(required=True)
        description = String(required=True)
        case_overview = String(required=False)
        organization_name = String(required=False)
        organization_type = String(required=False)
        practice_area = String(required=False)
        case_type = String(required=False)
        client_industry = String(required=False)
        case_duration = String(required=False)
        case_value = graphene.Decimal(required=False)
        outcome = String(required=False)
        awards_recognition = String(required=False)
        certifications = String(required=False)
        notable_mentions = String(required=False)
        featured_image = Upload(required=False)
        portfolio_document = Upload(required=False)
        is_featured = Boolean(required=False, default_value=False)
        is_confidential = Boolean(required=False, default_value=False)
        status = String(required=False, default_value='DRAFT')
    
    success = Boolean()
    message = String()
    portfolio = Field(PortfolioType)
    errors = graphene.List(String)
    
    @staticmethod
    @login_required
    @require_professional_user
    def mutate(root, info, **kwargs):
        try:
            user = info.context.user
            professional_profile = user.professional_profile
            
            portfolio_id = kwargs.pop('portfolio_id', None)
            featured_image = kwargs.pop('featured_image', None)
            portfolio_document = kwargs.pop('portfolio_document', None)
            
            if portfolio_id:
                # Update existing portfolio
                try:
                    portfolio = Portfolio.objects.get(
                        id=portfolio_id,
                        professional=professional_profile
                    )
                except Portfolio.DoesNotExist:
                    raise Http404("Portfolio not found")
            else:
                # Create new portfolio
                portfolio = Portfolio(professional=professional_profile)
            
            # Update text fields
            for field, value in kwargs.items():
                if hasattr(portfolio, field) and value is not None:
                    setattr(portfolio, field, value)
            
            # Handle file uploads
            mutation = UpdatePortfolioMutation()
            
            if featured_image:
                mutation.handle_file_upload(
                    featured_image, 
                    'featured_image', 
                    portfolio, 
                    file_type='image',
                    max_size_key='image'
                )
            
            if portfolio_document:
                mutation.handle_file_upload(
                    portfolio_document, 
                    'portfolio_document', 
                    portfolio, 
                    file_type='document',
                    max_size_key='document'
                )
            
            portfolio.save()
            
            # Update onboarding progress if this is the first portfolio
            if not portfolio_id and hasattr(professional_profile, 'onboarding_progress'):
                progress = professional_profile.onboarding_progress
                progress.mark_step_completed('PORTFOLIO_ADDED')
                progress.save()
            
            return UpdatePortfolioMutation(
                success=True,
                message="Portfolio updated successfully",
                portfolio=portfolio
            )
            
        except ValidationError as e:
            return UpdatePortfolioMutation(
                success=False,
                message="Validation error",
                errors=e.messages if hasattr(e, 'messages') else [str(e)]
            )
        except Http404 as e:
            return UpdatePortfolioMutation(
                success=False,
                message=str(e),
                errors=[str(e)]
            )
        except Exception as e:
            return UpdatePortfolioMutation(
                success=False,
                message="An error occurred while updating the portfolio",
                errors=[str(e)]
            )


# Aggregate mutations class
class FileMutations(ObjectType):
    """File-related mutations"""
    update_profile_picture = UpdateProfilePictureMutation.Field()
    remove_profile_picture = RemoveProfilePictureMutation.Field()
    upload_professional_document = UploadProfessionalDocumentMutation.Field()
    delete_professional_document = DeleteProfessionalDocumentMutation.Field()
    update_portfolio = UpdatePortfolioMutation.Field()
