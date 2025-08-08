import graphene
from graphene import ObjectType, Field, List, String, Boolean, ID, Int
from django.db.models import Q
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
    PaymentMethodType
)
from core.utils.permissions import professional_required


class ProfessionalQuery(ObjectType):
    # Step 1: Profile queries
    my_professional_profile = Field(ProfessionalProfileType)
    professional_profile = Field(ProfessionalProfileType, user_id=ID())
    professional_profiles = List(
        ProfessionalProfileType,
        verification_status=String(),
        area_of_expertise=String(),
        location=String(),
        first=Int(),
        skip=Int()
    )
    
    # Step 2: Document queries
    my_professional_documents = List(ProfessionalDocumentType)
    professional_documents = List(
        ProfessionalDocumentType, 
        professional_id=ID(),
        verification_status=String()
    )
    
    # Step 3: Video KYC queries
    my_video_kyc = Field(VideoKYCType)
    video_kyc_sessions = List(
        VideoKYCType,
        professional_id=ID(),
        status=String()
    )
    
    # Step 4: Portfolio queries
    my_portfolios = List(PortfolioType)
    portfolios = List(PortfolioType, professional_id=ID())
    portfolio = Field(PortfolioType, portfolio_id=ID(required=True))
    
    # Step 5: Consultation availability queries
    my_consultation_availability = Field(ConsultationAvailabilityType)
    consultation_availability = Field(ConsultationAvailabilityType, professional_id=ID())
    
    # Step 6: Payment method queries
    my_payment_methods = List(PaymentMethodType)
    payment_methods = List(PaymentMethodType, professional_id=ID())

    # Profile resolvers
    def resolve_my_professional_profile(self, info):
        """Get current user's professional profile"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return None
        
        try:
            return user.professional_profile
        except ProfessionalProfile.DoesNotExist:
            return None

    def resolve_professional_profile(self, info, user_id):
        """Get professional profile by user ID"""
        try:
            return ProfessionalProfile.objects.get(user__id=user_id)
        except ProfessionalProfile.DoesNotExist:
            return None

    def resolve_professional_profiles(self, info, verification_status=None, 
                                    area_of_expertise=None, location=None, 
                                    first=None, skip=None):
        """Get list of professional profiles with filters"""
        queryset = ProfessionalProfile.objects.select_related('user').all()
        
        # Apply filters
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        if area_of_expertise:
            queryset = queryset.filter(area_of_expertise=area_of_expertise)
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Apply pagination
        if skip:
            queryset = queryset[skip:]
        if first:
            queryset = queryset[:first]
        
        return queryset

    # Document resolvers
    def resolve_my_professional_documents(self, info):
        """Get current user's professional documents"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return []
        
        try:
            profile = user.professional_profile
            return ProfessionalDocument.objects.filter(professional=profile)
        except ProfessionalProfile.DoesNotExist:
            return []

    def resolve_professional_documents(self, info, professional_id=None, verification_status=None):
        """Get professional documents with filters"""
        queryset = ProfessionalDocument.objects.all()
        
        if professional_id:
            queryset = queryset.filter(professional__id=professional_id)
        
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        return queryset

    # Video KYC resolvers
    def resolve_my_video_kyc(self, info):
        """Get current user's video KYC session"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return None
        
        try:
            profile = user.professional_profile
            return VideoKYC.objects.filter(professional=profile).first()
        except ProfessionalProfile.DoesNotExist:
            return None

    def resolve_video_kyc_sessions(self, info, professional_id=None, status=None):
        """Get video KYC sessions with filters"""
        queryset = VideoKYC.objects.all()
        
        if professional_id:
            queryset = queryset.filter(professional__id=professional_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    # Portfolio resolvers
    def resolve_my_portfolios(self, info):
        """Get current user's portfolios"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return []
        
        try:
            profile = user.professional_profile
            return Portfolio.objects.filter(professional=profile)
        except ProfessionalProfile.DoesNotExist:
            return []

    def resolve_portfolios(self, info, professional_id):
        """Get portfolios by professional ID"""
        return Portfolio.objects.filter(professional__id=professional_id)

    def resolve_portfolio(self, info, portfolio_id):
        """Get specific portfolio by ID"""
        try:
            return Portfolio.objects.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            return None

    # Consultation availability resolvers
    def resolve_my_consultation_availability(self, info):
        """Get current user's consultation availability"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return None
        
        try:
            profile = user.professional_profile
            return ConsultationAvailability.objects.filter(professional=profile).first()
        except ProfessionalProfile.DoesNotExist:
            return None

    def resolve_consultation_availability(self, info, professional_id):
        """Get consultation availability by professional ID"""
        try:
            return ConsultationAvailability.objects.get(professional__id=professional_id)
        except ConsultationAvailability.DoesNotExist:
            return None

    # Payment method resolvers
    def resolve_my_payment_methods(self, info):
        """Get current user's payment methods"""
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return []
        
        try:
            profile = user.professional_profile
            return PaymentMethod.objects.filter(professional=profile)
        except ProfessionalProfile.DoesNotExist:
            return []

    def resolve_payment_methods(self, info, professional_id):
        """Get payment methods by professional ID"""
        return PaymentMethod.objects.filter(professional__id=professional_id)
