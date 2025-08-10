import graphene
from graphene_django import DjangoObjectType
from core.models import (
    ProfessionalProfile,
    ProfessionalDocument,
    VideoKYC,
    Portfolio,
    ConsultationAvailability,
    PaymentMethod,
    ProfessionalPricing,
    ProfessionalReviewSummary,
)
from core.types.file_types import FileInfoType
from core.types.common import ExpertiseAreaEnum


# Professional Profile Type
class ProfessionalProfileType(DjangoObjectType):
    """GraphQL type for ProfessionalProfile model"""
    area_of_expertise = graphene.String()
    areaOfExpertise = graphene.String()
    yearsOfExperience = graphene.String()
    bioIntroduction = graphene.String()
    onboardingStep = graphene.String()
    onboardingCompleted = graphene.Boolean()
    verificationStatus = graphene.String()
    createdAt = graphene.DateTime()
    updatedAt = graphene.DateTime()
    
    class Meta:
        model = ProfessionalProfile
        fields = (
            'id', 'user', 'area_of_expertise', 'years_of_experience',
            'bio_introduction', 'location', 'verification_status',
            'onboarding_step', 'onboarding_completed', 'created_at', 'updated_at',
            'pricing', 'review_summary'
        )
    
    def resolve_area_of_expertise(self, info):
        """Return the area_of_expertise as display value"""
        if not self.area_of_expertise:
            return None
        
        # Convert enum value to display value
        display_mapping = dict(ProfessionalProfile.EXPERTISE_AREA_CHOICES)
        return display_mapping.get(self.area_of_expertise, self.area_of_expertise)
    
    def resolve_areaOfExpertise(self, info):
        """Return the area_of_expertise as camelCase for frontend compatibility"""
        return self.resolve_area_of_expertise(info)
    
    def resolve_yearsOfExperience(self, info):
        """Return years_of_experience as camelCase"""
        return self.years_of_experience
    
    def resolve_bioIntroduction(self, info):
        """Return bio_introduction as camelCase"""
        return self.bio_introduction
    
    def resolve_onboardingStep(self, info):
        """Return onboarding_step as camelCase"""
        return self.onboarding_step
    
    def resolve_onboardingCompleted(self, info):
        """Return onboarding_completed as camelCase"""
        return self.onboarding_completed
    
    def resolve_verificationStatus(self, info):
        """Return verification_status as camelCase"""
        return self.verification_status
    
    def resolve_createdAt(self, info):
        """Return created_at as camelCase"""
        return self.created_at
    
    def resolve_updatedAt(self, info):
        """Return updated_at as camelCase"""
        return self.updated_at


class ProfessionalPricingType(DjangoObjectType):
    """GraphQL type for ProfessionalPricing model"""
    fee30Min = graphene.Float()
    fee60Min = graphene.Float() 
    fee90Min = graphene.Float()
    fee120Min = graphene.Float()
    acceptsOnline = graphene.Boolean()
    acceptsOffline = graphene.Boolean()
    offlineConsultationExtra = graphene.Float()
    
    class Meta:
        model = ProfessionalPricing
        fields = (
            'id', 'professional', 'fee_30_min', 'fee_60_min', 'fee_90_min', 'fee_120_min',
            'offline_consultation_extra', 'accepts_online', 'accepts_offline',
            'created_at', 'updated_at'
        )
    
    def resolve_fee30Min(self, info):
        """Return fee_30_min as camelCase"""
        return float(self.fee_30_min)
    
    def resolve_fee60Min(self, info):
        """Return fee_60_min as camelCase"""
        return float(self.fee_60_min)
    
    def resolve_fee90Min(self, info):
        """Return fee_90_min as camelCase"""
        return float(self.fee_90_min)
    
    def resolve_fee120Min(self, info):
        """Return fee_120_min as camelCase"""
        return float(self.fee_120_min)
    
    def resolve_acceptsOnline(self, info):
        """Return accepts_online as camelCase"""
        return self.accepts_online
    
    def resolve_acceptsOffline(self, info):
        """Return accepts_offline as camelCase"""
        return self.accepts_offline
    
    def resolve_offlineConsultationExtra(self, info):
        """Return offline_consultation_extra as camelCase"""
        return float(self.offline_consultation_extra)


class ProfessionalReviewSummaryType(DjangoObjectType):
    """GraphQL type for ProfessionalReviewSummary model"""
    averageRating = graphene.Float()
    totalReviews = graphene.Int()
    fiveStarCount = graphene.Int()
    fourStarCount = graphene.Int()
    threeStarCount = graphene.Int()
    twoStarCount = graphene.Int()
    oneStarCount = graphene.Int()
    lastUpdated = graphene.DateTime()
    
    class Meta:
        model = ProfessionalReviewSummary
        fields = (
            'id', 'professional', 'average_rating', 'total_reviews',
            'five_star_count', 'four_star_count', 'three_star_count',
            'two_star_count', 'one_star_count', 'last_updated'
        )
    
    def resolve_averageRating(self, info):
        """Return average_rating as camelCase"""
        return float(self.average_rating)
    
    def resolve_totalReviews(self, info):
        """Return total_reviews as camelCase"""
        return self.total_reviews
    
    def resolve_fiveStarCount(self, info):
        """Return five_star_count as camelCase"""
        return self.five_star_count
    
    def resolve_fourStarCount(self, info):
        """Return four_star_count as camelCase"""
        return self.four_star_count
    
    def resolve_threeStarCount(self, info):
        """Return three_star_count as camelCase"""
        return self.three_star_count
    
    def resolve_twoStarCount(self, info):
        """Return two_star_count as camelCase"""
        return self.two_star_count
    
    def resolve_oneStarCount(self, info):
        """Return one_star_count as camelCase"""
        return self.one_star_count
    
    def resolve_lastUpdated(self, info):
        """Return last_updated as camelCase"""
        return self.last_updated


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
    video = graphene.Field(FileInfoType)
    
    class Meta:
        model = VideoKYC
        fields = (
            'id', 'professional', 'status', 'completed_at', 
            'verified_at', 'created_at', 'session_data',
            # Exclude binary field: 'video_data'
            'video_name', 'video_content_type', 'video_size'
        )
    
    def resolve_video(self, info):
        return FileInfoType.from_instance(self, 'video')


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
    # Add camelCase aliases for frontend compatibility
    areaOfExpertise = graphene.String()
    years_of_experience = graphene.String()
    yearsOfExperience = graphene.String()
    bio_introduction = graphene.String()
    bioIntroduction = graphene.String()
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


# Alias for frontend compatibility
class PaymentDataInput(graphene.InputObjectType):
    """Input type for payment data (alias for PaymentMethodInputType)"""
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