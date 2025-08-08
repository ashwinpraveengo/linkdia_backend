import graphene
from graphene_django import DjangoObjectType
from core.models import (
    ProfessionalProfile,
    ProfessionalDocument,
    VideoKYC,
    Portfolio,
    ConsultationAvailability,
    PaymentMethod,
)
from core.types.file_types import FileInfoType


# Professional Profile Type
class ProfessionalProfileType(DjangoObjectType):
    """GraphQL type for ProfessionalProfile model"""
    
    class Meta:
        model = ProfessionalProfile
        fields = (
            'id', 'user', 'area_of_expertise', 'years_of_experience',
            'bio_introduction', 'location', 'verification_status',
            'onboarding_step', 'onboarding_completed', 'created_at', 'updated_at'
        )


# Step 2: Document Upload Types
class ProfessionalDocumentType(DjangoObjectType):
    """GraphQL type for ProfessionalDocument model"""
    document = graphene.Field(FileInfoType)
    
    class Meta:
        model = ProfessionalDocument
        fields = (
            'id', 'professional', 'document_type', 'verification_status',
            'uploaded_at', 'verified_at', 
            # Exclude binary field: 'document_data'
            'document_name', 'document_content_type', 'document_size'
        )
    
    def resolve_document(self, info):
        return FileInfoType.from_instance(self, 'document')


# Step 3: Video KYC Types  
class VideoKYCType(DjangoObjectType):
    """GraphQL type for VideoKYC model"""
    
    class Meta:
        model = VideoKYC
        fields = (
            'id', 'professional', 'status', 'completed_at', 
            'verified_at', 'created_at'
        )


# Step 4: Portfolio Types
class PortfolioType(DjangoObjectType):
    """GraphQL type for Portfolio model"""
    document = graphene.Field(FileInfoType)
    
    class Meta:
        model = Portfolio
        fields = (
            'id', 'professional', 'name', 
            # Exclude binary field: 'document_data'
            'document_name', 'document_content_type', 'document_size', 'created_at'
        )
    
    def resolve_document(self, info):
        return FileInfoType.from_instance(self, 'document')


# Step 5: Consultation Availability Types
class ConsultationAvailabilityType(DjangoObjectType):
    """GraphQL type for ConsultationAvailability model"""
    available_days = graphene.List(graphene.String)
    
    class Meta:
        model = ConsultationAvailability
        fields = (
            'id', 'professional', 'monday', 'tuesday', 'wednesday', 
            'thursday', 'friday', 'saturday', 'sunday', 'from_time', 
            'to_time', 'consultation_type', 'consultation_duration_minutes',
            'google_calendar_sync', 'outlook_calendar_sync', 'created_at', 'updated_at'
        )
    
    def resolve_available_days(self, info):
        return self.get_available_days()


# Step 6: Payment Method Types
class PaymentMethodType(DjangoObjectType):
    """GraphQL type for PaymentMethod model"""
    
    class Meta:
        model = PaymentMethod
        fields = (
            'id', 'professional', 'payment_type', 'account_holder_name',
            'bank_name', 'account_number', 'ifsc_code', 'wallet_provider',
            'wallet_phone_number', 'created_at', 'updated_at'
        )


# Input Types for mutations

class ProfessionalProfileInputType(graphene.InputObjectType):
    """Input type for professional profile updates"""
    area_of_expertise = graphene.String()
    years_of_experience = graphene.String()
    bio_introduction = graphene.String()
    location = graphene.String()


class ProfessionalDocumentInputType(graphene.InputObjectType):
    """Input type for professional document creation"""
    document_type = graphene.String(required=True)


class VideoKYCInputType(graphene.InputObjectType):
    """Input type for video KYC updates"""
    status = graphene.String()


class PortfolioInputType(graphene.InputObjectType):
    """Input type for portfolio creation"""
    name = graphene.String(required=True)


class ConsultationAvailabilityInputType(graphene.InputObjectType):
    """Input type for consultation availability setup"""
    monday = graphene.Boolean()
    tuesday = graphene.Boolean()
    wednesday = graphene.Boolean()
    thursday = graphene.Boolean()
    friday = graphene.Boolean()
    saturday = graphene.Boolean()
    sunday = graphene.Boolean()
    from_time = graphene.Time(required=True)
    to_time = graphene.Time(required=True)
    consultation_type = graphene.String(required=True)
    consultation_duration_minutes = graphene.Int(required=True)
    google_calendar_sync = graphene.Boolean()
    outlook_calendar_sync = graphene.Boolean()


class PaymentMethodInputType(graphene.InputObjectType):
    """Input type for payment method creation"""
    payment_type = graphene.String(required=True)
    # Bank account fields
    account_holder_name = graphene.String()
    bank_name = graphene.String()
    account_number = graphene.String()
    ifsc_code = graphene.String()
    # Digital wallet fields
    wallet_provider = graphene.String()
    wallet_phone_number = graphene.String()


# Additional Types Referenced in __init__.py

class OnboardingProgressType(graphene.ObjectType):
    """Type for onboarding progress tracking"""
    current_step = graphene.String()
    completed_steps = graphene.List(graphene.String)
    total_steps = graphene.Int()
    progress_percentage = graphene.Float()


class ProfessionalSettingsType(graphene.ObjectType):
    """Type for professional settings"""
    notification_enabled = graphene.Boolean()
    calendar_sync_enabled = graphene.Boolean()
    auto_accept_bookings = graphene.Boolean()


class ProfessionalSettingsInputType(graphene.InputObjectType):
    """Input type for professional settings"""
    notification_enabled = graphene.Boolean()
    calendar_sync_enabled = graphene.Boolean()
    auto_accept_bookings = graphene.Boolean()