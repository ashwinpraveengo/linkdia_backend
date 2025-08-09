import graphene
from graphene import ObjectType, Mutation, String, Boolean, Field, List, Int, DateTime, ID, Float
from graphene_file_upload.scalars import Upload
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.db import transaction
import base64
import logging

from core.models import (
    ProfessionalProfile, 
    ProfessionalDocument, 
    VideoKYC, 
    Portfolio, 
    ConsultationAvailability, 
    PaymentMethod,
)
from core.types.proffesional_profile import (
    ProfessionalProfileType,
    ProfessionalDocumentType,
    VideoKYCType,
    PortfolioType,
    ConsultationAvailabilityType,
    PaymentMethodType,
    ProfessionalProfileInputType,
    ProfessionalDocumentInputType,
    VideoKYCInputType,
    PortfolioInputType,
    ConsultationAvailabilityInputType,
    PaymentMethodInputType,
    PaymentDataInput,
)
from core.utils.permissions import professional_required
from core.utils.file_handlers import process_uploaded_file

User = get_user_model()
logger = logging.getLogger(__name__)


# Utility functions for step conversion
def get_step_number_from_name(step_name):
    """Convert step name to step number for frontend compatibility"""
    step_mapping = {
        'PROFILE_SETUP': 1,
        'DOCUMENT_UPLOAD': 2,
        'VIDEO_KYC': 3,
        'PORTFOLIO': 4,
        'CONSULTATION_HOURS': 5,
        'PAYMENT_SETUP': 6,
        'COMPLETED': 7
    }
    return step_mapping.get(step_name, 1)


def get_step_name_from_number(step_number):
    """Convert step number to step name for backend processing"""
    step_mapping = {
        1: 'PROFILE_SETUP',
        2: 'DOCUMENT_UPLOAD',
        3: 'VIDEO_KYC',
        4: 'PORTFOLIO',
        5: 'CONSULTATION_HOURS',
        6: 'PAYMENT_SETUP',
        7: 'COMPLETED'
    }
    return step_mapping.get(step_number, 'PROFILE_SETUP')


def get_completed_step_numbers(step_names):
    """Convert list of completed step names to numbers"""
    return [get_step_number_from_name(name) for name in step_names]


# Step 1: Profile Setup Mutations
class UpdateProfessionalProfile(Mutation):
    """Step 1: Update professional profile setup"""
    
    class Arguments:
        profile_data = ProfessionalProfileInputType(required=True)
        profile_picture = Upload()
    
    professional_profile = Field(ProfessionalProfileType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    

    @professional_required
    def mutate(self, info, profile_data, profile_picture=None):
        try:
            with transaction.atomic():
                user = info.context.user
                profile, created = ProfessionalProfile.objects.get_or_create(user=user)
                
                # Allow profile updates from PROFILE_SETUP or DOCUMENT_UPLOAD steps
                if profile.onboarding_step not in ['PROFILE_SETUP', 'DOCUMENT_UPLOAD']:
                    return UpdateProfessionalProfile(
                        success=False,
                        message=f"Cannot update profile from {profile.onboarding_step} step. Please complete current step first.",
                        current_step=profile.onboarding_step
                    )
                
                # Update profile fields with validation - support both camelCase and snake_case
                area_of_expertise = (profile_data.get('area_of_expertise') or 
                                   profile_data.get('areaOfExpertise'))
                if area_of_expertise:
                    # Validate area_of_expertise
                    valid_choices = [choice[0] for choice in ProfessionalProfile.EXPERTISE_AREA_CHOICES]
                    if area_of_expertise not in valid_choices:
                        return UpdateProfessionalProfile(
                            success=False,
                            message=f"Invalid area of expertise. Valid choices are: {', '.join(valid_choices)}",
                            current_step=profile.onboarding_step
                        )
                    profile.area_of_expertise = area_of_expertise
                
                years_of_experience = (profile_data.get('years_of_experience') or 
                                     profile_data.get('yearsOfExperience'))
                if years_of_experience:
                    profile.years_of_experience = years_of_experience
                
                bio_introduction = (profile_data.get('bio_introduction') or 
                                  profile_data.get('bioIntroduction'))
                if bio_introduction:
                    profile.bio_introduction = bio_introduction
            
                if profile_data.get('location'):
                    profile.location = profile_data['location']
                
                # Handle profile picture upload
                if profile_picture:
                    try:
                        file_data = process_uploaded_file(profile_picture)
                        user.profile_picture_data = file_data['data']
                        user.profile_picture_name = file_data['name']
                        user.profile_picture_content_type = file_data['content_type']
                        user.profile_picture_size = file_data['size']
                        user.save()
                    except Exception as file_error:
                        logger.error(f"Profile picture upload failed: {file_error}")
                        return UpdateProfessionalProfile(
                            success=False,
                            message="Failed to upload profile picture. Please try again.",
                            current_step=profile.onboarding_step
                        )
                
                # Check if profile setup is complete
                required_fields = ['area_of_expertise', 'years_of_experience', 'bio_introduction', 'location']
                has_profile_picture = bool(user.profile_picture_data)
                
                if all(getattr(profile, field) for field in required_fields) and has_profile_picture:
                    # Profile setup complete, move to next step only if currently on PROFILE_SETUP
                    if profile.onboarding_step == 'PROFILE_SETUP':
                        profile.update_onboarding_step('DOCUMENT_UPLOAD')
                        next_step = 'DOCUMENT_UPLOAD'
                        message = "Profile setup completed successfully! Please proceed to document upload."
                    else:
                        # User is updating profile from later step
                        next_step = profile.onboarding_step
                        message = "Profile updated successfully!"
                else:
                    # Profile incomplete, set back to PROFILE_SETUP if needed
                    if profile.onboarding_step != 'PROFILE_SETUP':
                        profile.update_onboarding_step('PROFILE_SETUP')
                    next_step = 'PROFILE_SETUP'
                    missing_items = []
                    for field in required_fields:
                        if not getattr(profile, field):
                            missing_items.append(field.replace('_', ' ').title())
                    if not has_profile_picture:
                        missing_items.append('Profile Picture')
                    
                    message = f"Profile updated. Please complete: {', '.join(missing_items)}"
                
                profile.save()
                
                return UpdateProfessionalProfile(
                    professional_profile=profile,
                    success=True,
                    message=message,
                    next_step=next_step,
                    current_step=profile.onboarding_step
                )
                
        except ValidationError as e:
            logger.warning(f"Validation error in profile update: {e}")
            return UpdateProfessionalProfile(
                success=False,
                message=str(e),
                current_step=profile.onboarding_step if 'profile' in locals() else 'PROFILE_SETUP'
            )
        except Exception as e:
            logger.error(f"Unexpected error in profile update: {e}")
            return UpdateProfessionalProfile(
                success=False,
                message="An unexpected error occurred. Please try again.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'PROFILE_SETUP'
            )

    # ...existing code...


# Step 2: Document Upload Mutations  
class UploadProfessionalDocument(Mutation):
    """Step 2: Upload professional document"""
    
    class Arguments:
        document_type = String(required=True)
        document_file = Upload(required=True)
    
    document = Field(ProfessionalDocumentType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    documents_count = Int()
    
    @professional_required
    def mutate(self, info, document_type, document_file):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return UploadProfessionalDocument(
                        success=False,
                        message="Professional profile not found. Please complete profile setup first.",
                        current_step='PROFILE_SETUP'
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step not in ['DOCUMENT_UPLOAD', 'PROFILE_SETUP']:
                    return UploadProfessionalDocument(
                        success=False,
                        message=f"Cannot upload documents from {profile.onboarding_step} step. Please complete steps in order.",
                        current_step=profile.onboarding_step
                    )
                
                # If coming from PROFILE_SETUP, move to DOCUMENT_UPLOAD
                if profile.onboarding_step == 'PROFILE_SETUP':
                    profile.update_onboarding_step('DOCUMENT_UPLOAD')
                
                # Validate document type
                valid_types = [choice[0] for choice in ProfessionalDocument.DOCUMENT_TYPE_CHOICES]
                if document_type not in valid_types:
                    return UploadProfessionalDocument(
                        success=False,
                        message=f"Invalid document type. Valid types: {', '.join(valid_types)}",
                        current_step=profile.onboarding_step
                    )
                
                # Process uploaded file
                try:
                    file_data = process_uploaded_file(document_file)
                except Exception as file_error:
                    logger.error(f"File processing failed: {file_error}")
                    return UploadProfessionalDocument(
                        success=False,
                        message="Failed to process uploaded file. Please check file format and try again.",
                        current_step=profile.onboarding_step
                    )
                
                # Create or update document
                document, created = ProfessionalDocument.objects.update_or_create(
                    professional=profile,
                    document_type=document_type,
                    defaults={
                        'document_data': file_data['data'],
                        'document_name': file_data['name'],
                        'document_content_type': file_data['content_type'],
                        'document_size': file_data['size'],
                        'verification_status': 'PENDING'
                    }
                )
                
                # Check total documents
                total_docs = ProfessionalDocument.objects.filter(professional=profile).count()
                
                if total_docs >= 2:
                    message = f"Document {'uploaded' if created else 'updated'} successfully. You have {total_docs} documents uploaded. Please wait for admin verification."
                    next_step = 'DOCUMENT_UPLOAD'  # Stay on same step until verified
                else:
                    message = f"Document {'uploaded' if created else 'updated'} successfully. Please upload at least {2 - total_docs} more document(s)."
                    next_step = 'DOCUMENT_UPLOAD'
                
                return UploadProfessionalDocument(
                    document=document,
                    success=True,
                    message=message,
                    next_step=next_step,
                    current_step=profile.onboarding_step,
                    documents_count=total_docs
                )
                
        except ValidationError as e:
            logger.warning(f"Validation error in document upload: {e}")
            return UploadProfessionalDocument(
                success=False,
                message=str(e),
                current_step=profile.onboarding_step if 'profile' in locals() else 'DOCUMENT_UPLOAD'
            )
        except Exception as e:
            logger.error(f"Unexpected error in document upload: {e}")
            return UploadProfessionalDocument(
                success=False,
                message="An unexpected error occurred. Please try again.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'DOCUMENT_UPLOAD'
            )


class VerifyProfessionalDocument(Mutation):
    """Admin mutation to verify professional documents"""
    
    class Arguments:
        document_id = ID(required=True)
        verification_status = String(required=True)  # VERIFIED, REJECTED
        admin_notes = String()  # Optional admin notes
    
    document = Field(ProfessionalDocumentType)
    success = Boolean()
    message = String()
    profile_updated = Boolean()
    next_step = String()
    
    def mutate(self, info, document_id, verification_status, admin_notes=None):
        try:
            with transaction.atomic():
                # Check if user is admin/staff
                if not info.context.user.is_staff:
                    return VerifyProfessionalDocument(
                        success=False,
                        message="Only admin can verify documents"
                    )
                
                # Validate verification status
                if verification_status not in ['VERIFIED', 'REJECTED']:
                    return VerifyProfessionalDocument(
                        success=False,
                        message="Invalid verification status. Use 'VERIFIED' or 'REJECTED'."
                    )
                
                document = ProfessionalDocument.objects.get(id=document_id)
                document.verification_status = verification_status
                
                if verification_status == 'VERIFIED':
                    document.verified_at = timezone.now()
                
                document.save()
                
                # Check if professional can move to next step
                profile = document.professional
                verified_docs = ProfessionalDocument.objects.filter(
                    professional=profile,
                    verification_status='VERIFIED'
                ).count()
                
                profile_updated = False
                next_step = profile.onboarding_step
                
                if verified_docs >= 2 and profile.onboarding_step == 'DOCUMENT_UPLOAD':
                    # Move to video KYC step
                    profile.update_onboarding_step('VIDEO_KYC')
                    profile_updated = True
                    next_step = 'VIDEO_KYC'
                    message = f"Document {verification_status.lower()} successfully. Professional can now proceed to Video KYC."
                else:
                    message = f"Document {verification_status.lower()} successfully. {verified_docs}/2 documents verified."
                
                return VerifyProfessionalDocument(
                    document=document,
                    success=True,
                    message=message,
                    profile_updated=profile_updated,
                    next_step=next_step
                )
                
        except ProfessionalDocument.DoesNotExist:
            return VerifyProfessionalDocument(
                success=False,
                message="Document not found"
            )
        except Exception as e:
            logger.error(f"Error in document verification: {e}")
            return VerifyProfessionalDocument(
                success=False,
                message="An unexpected error occurred during verification"
            )


# Step 3: Video KYC Mutations
class UploadVideoKYC(Mutation):
    """Step 3: Upload video KYC file"""
    
    class Arguments:
        video_file = Upload(required=True)
        session_data = String()  # Optional session metadata
    
    video_kyc = Field(VideoKYCType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    profile_updated = Boolean()
    
    @professional_required
    def mutate(self, info, video_file, session_data=None):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return UploadVideoKYC(
                        success=False,
                        message="Professional profile not found.",
                        current_step='PROFILE_SETUP',
                        profile_updated=False
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step != 'VIDEO_KYC':
                    return UploadVideoKYC(
                        success=False,
                        message=f"Cannot upload video KYC from {profile.onboarding_step} step. Please complete document verification first.",
                        current_step=profile.onboarding_step,
                        profile_updated=False
                    )
                
                # Verify that documents are verified (additional check)
                verified_docs = ProfessionalDocument.objects.filter(
                    professional=profile,
                    verification_status='VERIFIED'
                ).count()
                
                if verified_docs < 2:
                    return UploadVideoKYC(
                        success=False,
                        message="Please wait for at least 2 documents to be verified before uploading video KYC.",
                        current_step=profile.onboarding_step,
                        profile_updated=False
                    )
                
                # Process uploaded video file
                try:
                    file_data = process_uploaded_file(video_file, file_type='video', max_size_key='video')
                except Exception as file_error:
                    logger.error(f"Video KYC file processing failed: {file_error}")
                    return UploadVideoKYC(
                        success=False,
                        message="Failed to process uploaded video file. Please check file format and try again.",
                        current_step=profile.onboarding_step,
                        profile_updated=False
                    )
                
                # Create or update video KYC record with uploaded file
                video_kyc, created = VideoKYC.objects.get_or_create(    
                    professional=profile,
                    defaults={
                        'status': 'VERIFIED',  # Auto-verify immediately
                        'completed_at': timezone.now(),
                        'verified_at': timezone.now(),  # Set verification time
                        'video_data': file_data['data'],
                        'video_name': file_data['name'],
                        'video_content_type': file_data['content_type'],
                        'video_size': file_data['size'],
                        'session_data': session_data
                    }
                )
                
                if not created:
                    video_kyc.status = 'VERIFIED'  # Auto-verify
                    video_kyc.completed_at = timezone.now()
                    video_kyc.verified_at = timezone.now()
                    video_kyc.video_data = file_data['data']
                    video_kyc.video_name = file_data['name']
                    video_kyc.video_content_type = file_data['content_type']
                    video_kyc.video_size = file_data['size']
                    if session_data:
                        video_kyc.session_data = session_data
                    video_kyc.save()
                
                # Automatically move to portfolio step since KYC is auto-verified
                profile.update_onboarding_step('PORTFOLIO')
                
                return UploadVideoKYC(
                    video_kyc=video_kyc,
                    success=True,
                    message="Video KYC uploaded and automatically verified! You can now proceed to portfolio setup.",
                    next_step='PORTFOLIO',
                    current_step=profile.onboarding_step,
                    profile_updated=True
                )
                
        except Exception as e:
            logger.error(f"Error in video KYC upload: {e}")
            return UploadVideoKYC(
                success=False,
                message="An unexpected error occurred during video KYC upload.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'VIDEO_KYC',
                profile_updated=False
            )


class CompleteVideoKYC(Mutation):
    """Step 3: Complete video KYC"""
    
    class Arguments:
        session_data = String()  # Optional session metadata
    
    video_kyc = Field(VideoKYCType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    
    @professional_required
    def mutate(self, info, session_data=None):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return CompleteVideoKYC(
                        success=False,
                        message="Professional profile not found.",
                        current_step='PROFILE_SETUP'
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step != 'VIDEO_KYC':
                    return CompleteVideoKYC(
                        success=False,
                        message=f"Cannot complete video KYC from {profile.onboarding_step} step. Please complete document verification first.",
                        current_step=profile.onboarding_step
                    )
                
                # Verify that documents are verified (additional check)
                verified_docs = ProfessionalDocument.objects.filter(
                    professional=profile,
                    verification_status='VERIFIED'
                ).count()
                
                if verified_docs < 2:
                    return CompleteVideoKYC(
                        success=False,
                        message="Please wait for at least 2 documents to be verified before proceeding to video KYC.",
                        current_step=profile.onboarding_step
                    )
                
                # Create or update video KYC record
                video_kyc, created = VideoKYC.objects.get_or_create(    
                    professional=profile,
                    defaults={
                        'status': 'VERIFIED',  # Auto-verify immediately
                        'completed_at': timezone.now(),
                        'verified_at': timezone.now()  # Set verification time
                    }
                )
                
                if not created:
                    video_kyc.status = 'VERIFIED'  # Auto-verify
                    video_kyc.completed_at = timezone.now()
                    video_kyc.verified_at = timezone.now()
                    video_kyc.save()
                
                # Automatically move to portfolio step since KYC is auto-verified
                profile.update_onboarding_step('PORTFOLIO')
                
                return CompleteVideoKYC(
                    video_kyc=video_kyc,
                    success=True,
                    message="Video KYC completed and automatically verified! You can now proceed to portfolio setup.",
                    next_step='PORTFOLIO',
                    current_step=profile.onboarding_step
                )
                
        except Exception as e:
            logger.error(f"Error in video KYC completion: {e}")
            return CompleteVideoKYC(
                success=False,
                message="An unexpected error occurred during video KYC completion.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'VIDEO_KYC'
            )


class VerifyVideoKYC(Mutation):
    """Automatic video KYC verification (temporarily automatic for development)"""
    
    class Arguments:
        kyc_id = ID(required=True)
        status = String(required=False, default_value="VERIFIED")  # Auto-verify by default
        admin_notes = String()  # Optional admin notes
    
    video_kyc = Field(VideoKYCType)
    success = Boolean()
    message = String()
    profile_updated = Boolean()
    next_step = String()
    
    def mutate(self, info, kyc_id, status="VERIFIED", admin_notes=None):
        try:
            with transaction.atomic():
                # For now, make it automatic (remove admin check)
                # TODO: Re-enable admin check when manual verification is needed
                # if not info.context.user.is_staff:
                #     return VerifyVideoKYC(
                #         success=False,
                #         message="Only admin can verify KYC"
                #     )
                
                # Auto-verify all KYC for development purposes
                status = "VERIFIED"  # Force auto-verification
                
                video_kyc = VideoKYC.objects.get(id=kyc_id)
                video_kyc.status = status
                video_kyc.verified_at = timezone.now()
                
                # Move to portfolio step automatically
                profile = video_kyc.professional
                profile_updated = False
                next_step = profile.onboarding_step
                
                if profile.onboarding_step == 'VIDEO_KYC':
                    profile.update_onboarding_step('PORTFOLIO')
                    profile_updated = True
                    next_step = 'PORTFOLIO'
                    message = "Video KYC automatically verified successfully. You can now proceed to portfolio setup."
                else:
                    message = "Video KYC automatically verified successfully."
                
                video_kyc.save()
                
                return VerifyVideoKYC(
                    video_kyc=video_kyc,
                    success=True,
                    message=message,
                    profile_updated=profile_updated,
                    next_step=next_step
                )
                
        except VideoKYC.DoesNotExist:
            return VerifyVideoKYC(
                success=False,
                message="Video KYC record not found"
            )
        except Exception as e:
            logger.error(f"Error in video KYC verification: {e}")
            return VerifyVideoKYC(
                success=False,
                message="An unexpected error occurred during verification"
            )


# Step 4: Portfolio Mutations
class CreatePortfolio(Mutation):
    """Step 4: Create portfolio"""
    
    class Arguments:
        name = String(required=True)
        document_file = Upload(required=True)
    
    portfolio = Field(PortfolioType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    
    @professional_required
    def mutate(self, info, name, document_file):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return CreatePortfolio(
                        success=False,
                        message="Professional profile not found.",
                        current_step='PROFILE_SETUP'
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step != 'PORTFOLIO':
                    return CreatePortfolio(
                        success=False,
                        message=f"Cannot create portfolio from {profile.onboarding_step} step. Please complete video KYC verification first.",
                        current_step=profile.onboarding_step
                    )
                
                # Validate name length
                if len(name.strip()) < 3:
                    return CreatePortfolio(
                        success=False,
                        message="Portfolio name must be at least 3 characters long.",
                        current_step=profile.onboarding_step
                    )
                
                # Process uploaded file
                try:
                    file_data = process_uploaded_file(document_file)
                except Exception as file_error:
                    logger.error(f"Portfolio file processing failed: {file_error}")
                    return CreatePortfolio(
                        success=False,
                        message="Failed to process uploaded file. Please check file format and try again.",
                        current_step=profile.onboarding_step
                    )
                
                # Create portfolio
                portfolio = Portfolio.objects.create(
                    professional=profile,
                    name=name.strip(),
                    document_data=file_data['data'],
                    document_name=file_data['name'],
                    document_content_type=file_data['content_type'],
                    document_size=file_data['size']
                )
                
                # Move to next step
                profile.update_onboarding_step('CONSULTATION_HOURS')
                
                return CreatePortfolio(
                    portfolio=portfolio,
                    success=True,
                    message="Portfolio created successfully! Please proceed to set your consultation hours.",
                    next_step='CONSULTATION_HOURS',
                    current_step=profile.onboarding_step
                )
                
        except ValidationError as e:
            logger.warning(f"Validation error in portfolio creation: {e}")
            return CreatePortfolio(
                success=False,
                message=str(e),
                current_step=profile.onboarding_step if 'profile' in locals() else 'PORTFOLIO'
            )
        except Exception as e:
            logger.error(f"Unexpected error in portfolio creation: {e}")
            return CreatePortfolio(
                success=False,
                message="An unexpected error occurred. Please try again.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'PORTFOLIO'
            )


# Step 5: Consultation Hours Mutations
class SetConsultationAvailability(Mutation):
    """Step 5: Set consultation availability"""
    
    class Arguments:
        availability_data = ConsultationAvailabilityInputType(required=True)
    
    availability = Field(ConsultationAvailabilityType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    
    @professional_required
    def mutate(self, info, availability_data):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return SetConsultationAvailability(
                        success=False,
                        message="Professional profile not found.",
                        current_step='PROFILE_SETUP'
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step != 'CONSULTATION_HOURS':
                    return SetConsultationAvailability(
                        success=False,
                        message=f"Cannot set consultation hours from {profile.onboarding_step} step. Please complete portfolio setup first.",
                        current_step=profile.onboarding_step
                    )
                
                # Validate required fields
                if not availability_data.get('from_time') or not availability_data.get('to_time'):
                    return SetConsultationAvailability(
                        success=False,
                        message="From time and to time are required.",
                        current_step=profile.onboarding_step
                    )
                
                # Check if at least one day is selected
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if not any(availability_data.get(day) for day in days):
                    return SetConsultationAvailability(
                        success=False,
                        message="Please select at least one available day.",
                        current_step=profile.onboarding_step
                    )
                
                # Validate time range
                from_time = availability_data.get('from_time')
                to_time = availability_data.get('to_time')
                if from_time >= to_time:
                    return SetConsultationAvailability(
                        success=False,
                        message="End time must be after start time.",
                        current_step=profile.onboarding_step
                    )
                
                # Validate consultation duration
                duration = availability_data.get('consultation_duration_minutes', 60)
                valid_durations = [30, 60, 90, 120]
                if duration not in valid_durations:
                    return SetConsultationAvailability(
                        success=False,
                        message=f"Invalid consultation duration. Valid options: {valid_durations}",
                        current_step=profile.onboarding_step
                    )
                
                # Create or update availability
                availability, created = ConsultationAvailability.objects.update_or_create(
                    professional=profile,
                    defaults=availability_data
                )
                
                # Move to next step
                profile.update_onboarding_step('PAYMENT_SETUP')
                
                selected_days = [day.replace('_', ' ').title() for day in days if availability_data.get(day)]
                
                return SetConsultationAvailability(
                    availability=availability,
                    success=True,
                    message=f"Consultation availability set successfully for {', '.join(selected_days)}. Please proceed to payment setup.",
                    next_step='PAYMENT_SETUP',
                    current_step=profile.onboarding_step
                )
                
        except ValidationError as e:
            logger.warning(f"Validation error in consultation availability: {e}")
            return SetConsultationAvailability(
                success=False,
                message=str(e),
                current_step=profile.onboarding_step if 'profile' in locals() else 'CONSULTATION_HOURS'
            )
        except Exception as e:
            logger.error(f"Unexpected error in consultation availability: {e}")
            return SetConsultationAvailability(
                success=False,
                message="An unexpected error occurred. Please try again.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'CONSULTATION_HOURS'
            )


# Step 6: Payment Setup Mutations
class AddPaymentMethod(Mutation):
    """Step 6: Add payment method"""
    
    class Arguments:
        payment_data = PaymentDataInput(required=True)  # Changed to PaymentDataInput for frontend compatibility
    
    payment_method = Field(PaymentMethodType)
    success = Boolean()
    message = String()
    next_step = String()
    current_step = String()
    onboarding_completed = Boolean()
    
    @professional_required
    def mutate(self, info, payment_data):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    return AddPaymentMethod(
                        success=False,
                        message="Professional profile not found.",
                        current_step='PROFILE_SETUP',
                        onboarding_completed=False
                    )
                
                profile = user.professional_profile
                
                # Check if we're on the right step
                if profile.onboarding_step != 'PAYMENT_SETUP':
                    return AddPaymentMethod(
                        success=False,
                        message=f"Cannot add payment method from {profile.onboarding_step} step. Please complete consultation hours setup first.",
                        current_step=profile.onboarding_step,
                        onboarding_completed=False
                    )
                
                # Convert frontend field names to backend field names
                converted_data = {}
                field_mapping = {
                    'paymentType': 'payment_type',
                    'accountHolderName': 'account_holder_name',
                    'bankName': 'bank_name',
                    'accountNumber': 'account_number',
                    'ifscCode': 'ifsc_code',
                    'walletProvider': 'wallet_provider',
                    'walletPhoneNumber': 'wallet_phone_number'
                }
                
                # Map fields from frontend to backend format
                for frontend_field, backend_field in field_mapping.items():
                    if payment_data.get(frontend_field) is not None:
                        converted_data[backend_field] = payment_data[frontend_field]
                
                # Also handle the original format (snake_case) for backward compatibility
                for field in ['payment_type', 'account_holder_name', 'bank_name', 'account_number', 'ifsc_code', 'wallet_provider', 'wallet_phone_number']:
                    if payment_data.get(field) is not None:
                        converted_data[field] = payment_data[field]
                
                # Validate payment method data
                payment_type = converted_data.get('payment_type')
                
                if not payment_type:
                    return AddPaymentMethod(
                        success=False,
                        message="Payment type is required.",
                        current_step=profile.onboarding_step,
                        onboarding_completed=False
                    )
                
                if payment_type == 'BANK_ACCOUNT':
                    required_fields = ['account_holder_name', 'bank_name', 'account_number', 'ifsc_code']
                    missing_fields = [field for field in required_fields if not converted_data.get(field)]
                    if missing_fields:
                        missing_readable = [field.replace('_', ' ').title() for field in missing_fields]
                        return AddPaymentMethod(
                            success=False,
                            message=f"Missing required fields for bank account: {', '.join(missing_readable)}",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    # Additional validation for bank details
                    if len(converted_data.get('account_number', '')) < 8:
                        return AddPaymentMethod(
                            success=False,
                            message="Account number must be at least 8 digits.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    if len(converted_data.get('ifsc_code', '')) != 11:
                        return AddPaymentMethod(
                            success=False,
                            message="IFSC code must be exactly 11 characters.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                
                elif payment_type == 'DIGITAL_WALLET':
                    if not converted_data.get('wallet_provider') or not converted_data.get('wallet_phone_number'):
                        return AddPaymentMethod(
                            success=False,
                            message="Wallet provider and phone number are required for digital wallet.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    # Validate phone number format
                    phone = converted_data.get('wallet_phone_number', '')
                    # Handle formatted phone numbers like +919567894970
                    if phone.startswith('+91'):
                        phone = phone[3:]  # Remove +91
                        converted_data['wallet_phone_number'] = phone  # Update the converted data
                    elif phone.startswith('+'):
                        # Remove any other country code prefix for now
                        phone = phone[1:]
                        converted_data['wallet_phone_number'] = phone  # Update the converted data
                    
                    if not phone.isdigit() or len(phone) != 10:
                        return AddPaymentMethod(
                            success=False,
                            message="Phone number must be 10 digits (without country code).",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                
                else:
                    return AddPaymentMethod(
                        success=False,
                        message="Invalid payment type. Use 'BANK_ACCOUNT' or 'DIGITAL_WALLET'.",
                        current_step=profile.onboarding_step,
                        onboarding_completed=False
                    )
                
                # Create payment method with converted data
                payment_method = PaymentMethod.objects.create(
                    professional=profile,
                    **converted_data
                )
                
                # Complete onboarding
                profile.update_onboarding_step('COMPLETED')
                
                return AddPaymentMethod(
                    payment_method=payment_method,
                    success=True,
                    message="Payment method added successfully! Onboarding completed! You can now start receiving consultation bookings.",
                    next_step='COMPLETED',
                    current_step=profile.onboarding_step,
                    onboarding_completed=True
                )
                
        except ValidationError as e:
            logger.warning(f"Validation error in payment method: {e}")
            return AddPaymentMethod(
                success=False,
                message=str(e),
                current_step=profile.onboarding_step if 'profile' in locals() else 'PAYMENT_SETUP',
                onboarding_completed=False
            )
        except Exception as e:
            logger.error(f"Unexpected error in payment method: {e}")
            return AddPaymentMethod(
                success=False,
                message="An unexpected error occurred. Please try again.",
                current_step=profile.onboarding_step if 'profile' in locals() else 'PAYMENT_SETUP',
                onboarding_completed=False
            )


# Utility Mutations
class GetOnboardingStatus(graphene.ObjectType):
    """Get current onboarding status"""
    current_step = String()
    current_step_number = Int()  # Added for frontend compatibility
    onboarding_completed = Boolean()
    steps_completed = List(String)
    steps_completed_numbers = List(Int)  # Added for frontend compatibility
    next_step_message = String()
    progress_percentage = Float()
    total_steps = Int()
    can_proceed = Boolean()
    blocking_issues = List(String)


class CheckOnboardingStatus(Mutation):
    """Check current onboarding status"""
    
    class Arguments:
        pass
    
    status = Field(GetOnboardingStatus)
    success = Boolean()
    message = String()
    
    @professional_required
    def mutate(self, info):
        try:
            user = info.context.user
            
            # Ensure user has professional profile
            if not hasattr(user, 'professional_profile'):
                # Create profile if it doesn't exist
                profile = ProfessionalProfile.objects.create(user=user)
            else:
                profile = user.professional_profile
            
            # Determine completed steps and blocking issues
            steps_completed = []
            blocking_issues = []
            
            # Step 1: Profile Setup
            required_fields = ['area_of_expertise', 'years_of_experience', 'bio_introduction', 'location']
            has_profile_picture = bool(user.profile_picture_data)
            missing_profile_items = []
            
            for field in required_fields:
                if not getattr(profile, field):
                    missing_profile_items.append(field.replace('_', ' ').title())
            
            if not has_profile_picture:
                missing_profile_items.append('Profile Picture')
            
            if not missing_profile_items:
                steps_completed.append('PROFILE_SETUP')
            elif profile.onboarding_step == 'PROFILE_SETUP':
                blocking_issues.extend([f"Missing: {item}" for item in missing_profile_items])
            
            # Step 2: Document Upload
            total_docs = ProfessionalDocument.objects.filter(professional=profile).count()
            verified_docs = ProfessionalDocument.objects.filter(
                professional=profile,
                verification_status='VERIFIED'
            ).count()
            pending_docs = ProfessionalDocument.objects.filter(
                professional=profile,
                verification_status='PENDING'
            ).count()
            rejected_docs = ProfessionalDocument.objects.filter(
                professional=profile,
                verification_status='REJECTED'
            ).count()
            
            if verified_docs >= 2:
                steps_completed.append('DOCUMENT_UPLOAD')
            elif profile.onboarding_step == 'DOCUMENT_UPLOAD':
                if total_docs < 2:
                    blocking_issues.append(f"Need to upload {2 - total_docs} more document(s)")
                elif pending_docs > 0:
                    blocking_issues.append(f"{pending_docs} document(s) pending admin verification")
                elif rejected_docs > 0:
                    blocking_issues.append(f"{rejected_docs} document(s) rejected - please re-upload")
            
            # Step 3: Video KYC (Auto-verified for now)
            video_kyc = VideoKYC.objects.filter(professional=profile).first()
            if video_kyc and video_kyc.status == 'VERIFIED':
                steps_completed.append('VIDEO_KYC')
            elif profile.onboarding_step == 'VIDEO_KYC':
                if not video_kyc:
                    blocking_issues.append("Video KYC session not completed")
                # Note: Removed manual verification checks since it's now automatic
            
            # Step 4: Portfolio
            portfolio = Portfolio.objects.filter(professional=profile).first()
            if portfolio:
                steps_completed.append('PORTFOLIO')
            elif profile.onboarding_step == 'PORTFOLIO':
                blocking_issues.append("Portfolio not created")
            
            # Step 5: Consultation Hours
            availability = ConsultationAvailability.objects.filter(professional=profile).first()
            if availability:
                steps_completed.append('CONSULTATION_HOURS')
            elif profile.onboarding_step == 'CONSULTATION_HOURS':
                blocking_issues.append("Consultation availability not set")
            
            # Step 6: Payment Setup
            payment_method = PaymentMethod.objects.filter(professional=profile).first()
            if payment_method:
                steps_completed.append('PAYMENT_SETUP')
            elif profile.onboarding_step == 'PAYMENT_SETUP':
                blocking_issues.append("Payment method not added")
            
            # Calculate progress
            total_steps = 6
            progress_percentage = (len(steps_completed) / total_steps) * 100
            can_proceed = len(blocking_issues) == 0
            
            # Generate next step message
            step_messages = {
                'PROFILE_SETUP': 'Complete your profile with picture, expertise, experience, bio, and location',
                'DOCUMENT_UPLOAD': 'Upload at least 2 documents for verification',
                'VIDEO_KYC': 'Complete video KYC verification session (automatically verified)',
                'PORTFOLIO': 'Add your portfolio with a sample document',
                'CONSULTATION_HOURS': 'Set your consultation availability hours',
                'PAYMENT_SETUP': 'Add your payment method details',
                'COMPLETED': 'All steps completed! You can now receive consultations'
            }
            
            next_step_message = step_messages.get(profile.onboarding_step, '')
            
            # Convert to numeric values for frontend compatibility
            current_step_number = get_step_number_from_name(profile.onboarding_step)
            steps_completed_numbers = get_completed_step_numbers(steps_completed)
            
            status = GetOnboardingStatus(
                current_step=profile.onboarding_step,
                current_step_number=current_step_number,
                onboarding_completed=profile.onboarding_completed,
                steps_completed=steps_completed,
                steps_completed_numbers=steps_completed_numbers,
                next_step_message=next_step_message,
                progress_percentage=progress_percentage,
                total_steps=total_steps,
                can_proceed=can_proceed,
                blocking_issues=blocking_issues
            )
            
            return CheckOnboardingStatus(
                status=status,
                success=True,
                message="Onboarding status retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in checking onboarding status: {e}")
            return CheckOnboardingStatus(
                success=False,
                message="An unexpected error occurred while checking status"
            )


class MarkStepCompleted(Mutation):
    """Mark a specific onboarding step as completed"""
    
    class Arguments:
        step_number = Int(required=True)
    
    success = Boolean()
    message = String()
    current_step = Int()
    current_step_name = String()
    steps_completed = List(Int)
    next_step = String()
    
    @professional_required
    def mutate(self, info, step_number):
        try:
            with transaction.atomic():
                user = info.context.user
                
                # Ensure user has professional profile
                if not hasattr(user, 'professional_profile'):
                    profile = ProfessionalProfile.objects.create(user=user)
                else:
                    profile = user.professional_profile
                
                # Convert step number to step name
                step_name = get_step_name_from_number(step_number)
                
                # Validate step number
                if step_number < 1 or step_number > 6:
                    return MarkStepCompleted(
                        success=False,
                        message="Invalid step number. Must be between 1 and 6.",
                        current_step=get_step_number_from_name(profile.onboarding_step),
                        current_step_name=profile.onboarding_step
                    )
                
                # Check if step can be completed based on current progress
                current_step_number = get_step_number_from_name(profile.onboarding_step)
                
                # Allow completing current step or previous steps for editing
                if step_number > current_step_number + 1:
                    return MarkStepCompleted(
                        success=False,
                        message=f"Cannot complete step {step_number} yet. Please complete step {current_step_number} first.",
                        current_step=current_step_number,
                        current_step_name=profile.onboarding_step
                    )
                
                # Check if the step requirements are actually met
                step_requirements_met = False
                error_message = ""
                
                if step_number == 1:  # Profile Setup
                    required_fields = ['area_of_expertise', 'years_of_experience', 'bio_introduction', 'location']
                    has_profile_picture = bool(user.profile_picture_data)
                    missing_items = [field for field in required_fields if not getattr(profile, field)]
                    
                    if not missing_items and has_profile_picture:
                        step_requirements_met = True
                        if profile.onboarding_step == 'PROFILE_SETUP':
                            profile.update_onboarding_step('DOCUMENT_UPLOAD')
                    else:
                        error_message = f"Profile setup not complete. Missing: {', '.join(missing_items + (['Profile Picture'] if not has_profile_picture else []))}"
                
                elif step_number == 2:  # Document Upload
                    verified_docs = ProfessionalDocument.objects.filter(
                        professional=profile,
                        verification_status='VERIFIED'
                    ).count()
                    
                    if verified_docs >= 2:
                        step_requirements_met = True
                        if profile.onboarding_step == 'DOCUMENT_UPLOAD':
                            profile.update_onboarding_step('VIDEO_KYC')
                    else:
                        error_message = f"Need {2 - verified_docs} more verified documents to complete this step"
                
                elif step_number == 3:  # Video KYC (Auto-verified)
                    video_kyc = VideoKYC.objects.filter(professional=profile).first()
                    
                    if video_kyc and video_kyc.status == 'VERIFIED':
                        step_requirements_met = True
                        if profile.onboarding_step == 'VIDEO_KYC':
                            profile.update_onboarding_step('PORTFOLIO')
                    else:
                        if not video_kyc:
                            error_message = "Video KYC session not completed"
                        else:
                            error_message = "Video KYC not completed yet"
                
                elif step_number == 4:  # Portfolio
                    portfolio = Portfolio.objects.filter(professional=profile).first()
                    
                    if portfolio:
                        step_requirements_met = True
                        if profile.onboarding_step == 'PORTFOLIO':
                            profile.update_onboarding_step('CONSULTATION_HOURS')
                    else:
                        error_message = "Portfolio not created yet"
                
                elif step_number == 5:  # Consultation Hours
                    availability = ConsultationAvailability.objects.filter(professional=profile).first()
                    
                    if availability:
                        step_requirements_met = True
                        if profile.onboarding_step == 'CONSULTATION_HOURS':
                            profile.update_onboarding_step('PAYMENT_SETUP')
                    else:
                        error_message = "Consultation availability not set"
                
                elif step_number == 6:  # Payment Setup
                    payment_method = PaymentMethod.objects.filter(professional=profile).first()
                    
                    if payment_method:
                        step_requirements_met = True
                        if profile.onboarding_step == 'PAYMENT_SETUP':
                            profile.update_onboarding_step('COMPLETED')
                    else:
                        error_message = "Payment method not added"
                
                if not step_requirements_met:
                    return MarkStepCompleted(
                        success=False,
                        message=error_message or f"Step {step_number} requirements not met",
                        current_step=get_step_number_from_name(profile.onboarding_step),
                        current_step_name=profile.onboarding_step
                    )
                
                # Get updated completed steps
                steps_completed = []
                
                # Check all steps again to get accurate completed list
                # Step 1
                required_fields = ['area_of_expertise', 'years_of_experience', 'bio_introduction', 'location']
                has_profile_picture = bool(user.profile_picture_data)
                if all(getattr(profile, field) for field in required_fields) and has_profile_picture:
                    steps_completed.append(1)
                
                # Step 2
                verified_docs = ProfessionalDocument.objects.filter(
                    professional=profile,
                    verification_status='VERIFIED'
                ).count()
                if verified_docs >= 2:
                    steps_completed.append(2)
                
                # Step 3
                video_kyc = VideoKYC.objects.filter(professional=profile).first()
                if video_kyc and video_kyc.status == 'VERIFIED':
                    steps_completed.append(3)
                
                # Step 4
                portfolio = Portfolio.objects.filter(professional=profile).first()
                if portfolio:
                    steps_completed.append(4)
                
                # Step 5
                availability = ConsultationAvailability.objects.filter(professional=profile).first()
                if availability:
                    steps_completed.append(5)
                
                # Step 6
                payment_method = PaymentMethod.objects.filter(professional=profile).first()
                if payment_method:
                    steps_completed.append(6)
                
                current_step_number = get_step_number_from_name(profile.onboarding_step)
                
                return MarkStepCompleted(
                    success=True,
                    message=f"Step {step_number} marked as completed successfully",
                    current_step=current_step_number,
                    current_step_name=profile.onboarding_step,
                    steps_completed=steps_completed,
                    next_step=profile.onboarding_step
                )
                
        except Exception as e:
            logger.error(f"Error in mark step completed: {e}")
            return MarkStepCompleted(
                success=False,
                message="An unexpected error occurred while updating step status"
            )


# Mutation class that combines all mutations
class ProfessionalOnboardingMutations(ObjectType):
    # Step 1: Profile Setup
    update_professional_profile = UpdateProfessionalProfile.Field()
    
    # Step 2: Document Upload
    upload_professional_document = UploadProfessionalDocument.Field()
    verify_professional_document = VerifyProfessionalDocument.Field()  # Admin only
    
    # Step 3: Video KYC
    upload_video_kyc = UploadVideoKYC.Field()
    complete_video_kyc = CompleteVideoKYC.Field()
    verify_video_kyc = VerifyVideoKYC.Field()  # Admin only
    
    # Step 4: Portfolio
    create_portfolio = CreatePortfolio.Field()
    
    # Step 5: Consultation Hours
    set_consultation_availability = SetConsultationAvailability.Field()
    
    # Step 6: Payment Setup
    add_payment_method = AddPaymentMethod.Field()
    
    # Utility
    check_onboarding_status = CheckOnboardingStatus.Field()
    mark_step_completed = MarkStepCompleted.Field()
