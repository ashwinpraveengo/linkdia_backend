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
)
from core.utils.permissions import professional_required
from core.utils.file_handlers import process_uploaded_file

User = get_user_model()
logger = logging.getLogger(__name__)


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
                
                # Ensure we're on the correct step
                if profile.onboarding_step not in ['PROFILE_SETUP']:
                    return UpdateProfessionalProfile(
                        success=False,
                        message=f"Cannot update profile from {profile.onboarding_step} step. Please complete steps in order.",
                        current_step=profile.onboarding_step
                    )
                
                # Update profile fields
                for field, value in profile_data.items():
                    if hasattr(profile, field) and value is not None:
                        setattr(profile, field, value)
                
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
                    # Profile setup complete, move to next step
                    profile.update_onboarding_step('DOCUMENT_UPLOAD')
                    next_step = 'DOCUMENT_UPLOAD'
                    message = "Profile setup completed successfully! Please proceed to document upload."
                else:
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
                        'status': 'COMPLETED',
                        'completed_at': timezone.now()
                    }
                )
                
                if not created:
                    video_kyc.status = 'COMPLETED'
                    video_kyc.completed_at = timezone.now()
                    video_kyc.save()
                
                return CompleteVideoKYC(
                    video_kyc=video_kyc,
                    success=True,
                    message="Video KYC completed successfully. Please wait for admin verification.",
                    next_step='VIDEO_KYC',  # Stay on same step until verified
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
    """Admin mutation to verify video KYC"""
    
    class Arguments:
        kyc_id = ID(required=True)
        status = String(required=True)  # VERIFIED, REJECTED
        admin_notes = String()  # Optional admin notes
    
    video_kyc = Field(VideoKYCType)
    success = Boolean()
    message = String()
    profile_updated = Boolean()
    next_step = String()
    
    def mutate(self, info, kyc_id, status, admin_notes=None):
        try:
            with transaction.atomic():
                # Check if user is admin/staff
                if not info.context.user.is_staff:
                    return VerifyVideoKYC(
                        success=False,
                        message="Only admin can verify KYC"
                    )
                
                # Validate status
                if status not in ['VERIFIED', 'REJECTED']:
                    return VerifyVideoKYC(
                        success=False,
                        message="Invalid status. Use 'VERIFIED' or 'REJECTED'."
                    )
                
                video_kyc = VideoKYC.objects.get(id=kyc_id)
                video_kyc.status = status
                
                profile_updated = False
                next_step = video_kyc.professional.onboarding_step
                
                if status == 'VERIFIED':
                    video_kyc.verified_at = timezone.now()
                    
                    # Move to portfolio step
                    profile = video_kyc.professional
                    if profile.onboarding_step == 'VIDEO_KYC':
                        profile.update_onboarding_step('PORTFOLIO')
                        profile_updated = True
                        next_step = 'PORTFOLIO'
                        message = f"Video KYC verified successfully. Professional can now proceed to portfolio setup."
                    else:
                        message = f"Video KYC verified successfully."
                else:
                    message = f"Video KYC rejected. Professional needs to redo video KYC."
                
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
        payment_data = PaymentMethodInputType(required=True)
    
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
                
                # Validate payment method data
                payment_type = payment_data.get('payment_type')
                
                if not payment_type:
                    return AddPaymentMethod(
                        success=False,
                        message="Payment type is required.",
                        current_step=profile.onboarding_step,
                        onboarding_completed=False
                    )
                
                if payment_type == 'BANK_ACCOUNT':
                    required_fields = ['account_holder_name', 'bank_name', 'account_number', 'ifsc_code']
                    missing_fields = [field for field in required_fields if not payment_data.get(field)]
                    if missing_fields:
                        missing_readable = [field.replace('_', ' ').title() for field in missing_fields]
                        return AddPaymentMethod(
                            success=False,
                            message=f"Missing required fields for bank account: {', '.join(missing_readable)}",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    # Additional validation for bank details
                    if len(payment_data.get('account_number', '')) < 8:
                        return AddPaymentMethod(
                            success=False,
                            message="Account number must be at least 8 digits.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    if len(payment_data.get('ifsc_code', '')) != 11:
                        return AddPaymentMethod(
                            success=False,
                            message="IFSC code must be exactly 11 characters.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                
                elif payment_type == 'DIGITAL_WALLET':
                    if not payment_data.get('wallet_provider') or not payment_data.get('wallet_phone_number'):
                        return AddPaymentMethod(
                            success=False,
                            message="Wallet provider and phone number are required for digital wallet.",
                            current_step=profile.onboarding_step,
                            onboarding_completed=False
                        )
                    
                    # Validate phone number format
                    phone = payment_data.get('wallet_phone_number', '')
                    if not phone.isdigit() or len(phone) != 10:
                        return AddPaymentMethod(
                            success=False,
                            message="Phone number must be 10 digits.",
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
                
                # Create payment method
                payment_method = PaymentMethod.objects.create(
                    professional=profile,
                    **payment_data
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
    onboarding_completed = Boolean()
    steps_completed = List(String)
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
            
            # Step 3: Video KYC
            video_kyc = VideoKYC.objects.filter(professional=profile).first()
            if video_kyc and video_kyc.status == 'VERIFIED':
                steps_completed.append('VIDEO_KYC')
            elif profile.onboarding_step == 'VIDEO_KYC':
                if not video_kyc:
                    blocking_issues.append("Video KYC session not completed")
                elif video_kyc.status == 'COMPLETED':
                    blocking_issues.append("Video KYC completed, waiting for admin verification")
                elif video_kyc.status == 'REJECTED':
                    blocking_issues.append("Video KYC rejected - please redo")
            
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
                'VIDEO_KYC': 'Complete video KYC verification session',
                'PORTFOLIO': 'Add your portfolio with a sample document',
                'CONSULTATION_HOURS': 'Set your consultation availability hours',
                'PAYMENT_SETUP': 'Add your payment method details',
                'COMPLETED': 'All steps completed! You can now receive consultations'
            }
            
            next_step_message = step_messages.get(profile.onboarding_step, '')
            
            status = GetOnboardingStatus(
                current_step=profile.onboarding_step,
                onboarding_completed=profile.onboarding_completed,
                steps_completed=steps_completed,
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


# Mutation class that combines all mutations
class ProfessionalOnboardingMutations(ObjectType):
    # Step 1: Profile Setup
    update_professional_profile = UpdateProfessionalProfile.Field()
    
    # Step 2: Document Upload
    upload_professional_document = UploadProfessionalDocument.Field()
    verify_professional_document = VerifyProfessionalDocument.Field()  # Admin only
    
    # Step 3: Video KYC
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
