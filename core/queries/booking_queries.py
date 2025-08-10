import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import (
    ConsultationBooking, ConsultationSlot, ProfessionalReview, 
    ProfessionalReviewSummary, ProfessionalProfile, CustomUser
)
from core.utils.permissions import login_required
from core.types.common import PaginatedResult
from core.types.proffesional_profile import ProfessionalProfileType, ProfessionalReviewSummaryType


class ConsultationBookingType(DjangoObjectType):
    can_be_cancelled_by_client = graphene.Boolean()
    can_be_cancelled_by_professional = graphene.Boolean()
    
    class Meta:
        model = ConsultationBooking
        fields = "__all__"
    
    def resolve_can_be_cancelled_by_client(self, info):
        return self.can_be_cancelled_by_client()
    
    def resolve_can_be_cancelled_by_professional(self, info):
        return self.can_be_cancelled_by_professional()


class ConsultationSlotType(DjangoObjectType):
    is_available = graphene.Boolean()
    duration_minutes = graphene.Int()
    
    class Meta:
        model = ConsultationSlot
        fields = "__all__"
    
    def resolve_is_available(self, info):
        return self.is_available()
    
    def resolve_duration_minutes(self, info):
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)


class ProfessionalReviewType(DjangoObjectType):
    class Meta:
        model = ProfessionalReview
        fields = "__all__"


class ProfessionalReviewSummaryType(DjangoObjectType):
    class Meta:
        model = ProfessionalReviewSummary
        fields = "__all__"


class PaginatedBookingsType(PaginatedResult):
    items = graphene.List(ConsultationBookingType)


class PaginatedReviewsType(PaginatedResult):
    items = graphene.List(ProfessionalReviewType)


class PaginatedSlotsType(PaginatedResult):
    items = graphene.List(ConsultationSlotType)


class PaginatedProfessionalsType(PaginatedResult):
    items = graphene.List(ProfessionalProfileType)


class BookingQueries(graphene.ObjectType):
    # Booking Queries
    my_bookings = graphene.Field(
        PaginatedBookingsType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        status=graphene.String(),
        description="Get current user's bookings"
    )
    
    professional_bookings = graphene.Field(
        PaginatedBookingsType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        status=graphene.String(),
        description="Get bookings for the professional"
    )
    
    booking_detail = graphene.Field(
        ConsultationBookingType,
        booking_id=graphene.UUID(required=True),
        description="Get booking details by ID"
    )
    
    # Slot Availability Queries
    available_slots = graphene.Field(
        PaginatedSlotsType,
        professional_id=graphene.UUID(required=True),
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        description="Get available consultation slots for a professional"
    )
    
    professional_slots = graphene.Field(
        PaginatedSlotsType,
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        status=graphene.String(),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        description="Get slots for the professional (professional only)"
    )
    
    # Review Queries
    professional_reviews = graphene.Field(
        PaginatedReviewsType,
        professional_id=graphene.UUID(required=True),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        rating_filter=graphene.Int(),
        description="Get reviews for a professional"
    )
    
    my_reviews = graphene.Field(
        PaginatedReviewsType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        description="Get reviews written by current user"
    )
    
    review_detail = graphene.Field(
        ProfessionalReviewType,
        review_id=graphene.UUID(required=True),
        description="Get review details by ID"
    )
    
    professional_review_summary = graphene.Field(
        ProfessionalReviewSummaryType,
        professional_id=graphene.UUID(required=True),
        description="Get aggregated review statistics for a professional"
    )
    
    # Search and Browse Queries for Clients
    verified_professionals = graphene.Field(
        PaginatedProfessionalsType,
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        area_of_expertise=graphene.String(),
        location=graphene.String(),
        min_rating=graphene.Float(),
        search_text=graphene.String(),
        description="Get verified professionals for client browsing"
    )

    @login_required
    def resolve_my_bookings(self, info, page=1, page_size=10, status=None):
        user = info.context.user
        
        bookings = ConsultationBooking.objects.filter(client=user)
        
        if status:
            bookings = bookings.filter(booking_status=status.upper())
        
        bookings = bookings.order_by('-created_at')
        
        # Pagination
        total = bookings.count()
        start = (page - 1) * page_size
        end = start + page_size
        bookings = bookings[start:end]
        
        return PaginatedBookingsType(
            items=bookings,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    @login_required
    def resolve_professional_bookings(self, info, page=1, page_size=10, status=None):
        user = info.context.user
        
        if not user.is_professional:
            raise Exception("Only professionals can access this data")
        
        try:
            professional_profile = user.professional_profile
        except:
            raise Exception("Professional profile not found")
        
        bookings = ConsultationBooking.objects.filter(professional=professional_profile)
        
        if status:
            bookings = bookings.filter(booking_status=status.upper())
        
        bookings = bookings.order_by('-created_at')
        
        # Pagination
        total = bookings.count()
        start = (page - 1) * page_size
        end = start + page_size
        bookings = bookings[start:end]
        
        return PaginatedBookingsType(
            items=bookings,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    @login_required
    def resolve_booking_detail(self, info, booking_id):
        user = info.context.user
        
        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            
            # Check permission
            if booking.client != user and (not user.is_professional or booking.professional.user != user):
                raise Exception("Permission denied")
            
            return booking
        except ConsultationBooking.DoesNotExist:
            raise Exception("Booking not found")

    def resolve_available_slots(self, info, professional_id, date_from=None, date_to=None, page=1, page_size=20):
        try:
            professional = ProfessionalProfile.objects.get(id=professional_id)
        except ProfessionalProfile.DoesNotExist:
            raise Exception("Professional not found")
        
        # Check if professional is verified
        if professional.verification_status != 'VERIFIED':
            raise Exception("Only verified professionals are available for booking")
        
        slots = ConsultationSlot.objects.filter(
            professional=professional,
            status='AVAILABLE'
        )
        
        # Date filtering
        if date_from:
            slots = slots.filter(start_time__date__gte=date_from)
        if date_to:
            slots = slots.filter(start_time__date__lte=date_to)
        
        # Only show future slots
        slots = slots.filter(start_time__gt=timezone.now())
        slots = slots.order_by('start_time')
        
        # Pagination
        total = slots.count()
        start = (page - 1) * page_size
        end = start + page_size
        slots = slots[start:end]
        
        return PaginatedSlotsType(
            items=slots,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    @login_required
    def resolve_professional_slots(self, info, date_from=None, date_to=None, status=None, page=1, page_size=20):
        user = info.context.user
        
        if not user.is_professional:
            raise Exception("Only professionals can access this data")
        
        try:
            professional_profile = user.professional_profile
        except:
            raise Exception("Professional profile not found")
        
        slots = ConsultationSlot.objects.filter(professional=professional_profile)
        
        # Filters
        if date_from:
            slots = slots.filter(start_time__date__gte=date_from)
        if date_to:
            slots = slots.filter(start_time__date__lte=date_to)
        if status:
            slots = slots.filter(status=status.upper())
        
        slots = slots.order_by('start_time')
        
        # Pagination
        total = slots.count()
        start = (page - 1) * page_size
        end = start + page_size
        slots = slots[start:end]
        
        return PaginatedSlotsType(
            items=slots,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    def resolve_professional_reviews(self, info, professional_id, page=1, page_size=10, rating_filter=None):
        try:
            professional = ProfessionalProfile.objects.get(id=professional_id)
        except ProfessionalProfile.DoesNotExist:
            raise Exception("Professional not found")
        
        reviews = ProfessionalReview.objects.filter(professional=professional)
        
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)
        
        reviews = reviews.order_by('-created_at')
        
        # Pagination
        total = reviews.count()
        start = (page - 1) * page_size
        end = start + page_size
        reviews = reviews[start:end]
        
        return PaginatedReviewsType(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    @login_required
    def resolve_my_reviews(self, info, page=1, page_size=10):
        user = info.context.user
        
        reviews = ProfessionalReview.objects.filter(client=user)
        reviews = reviews.order_by('-created_at')
        
        # Pagination
        total = reviews.count()
        start = (page - 1) * page_size
        end = start + page_size
        reviews = reviews[start:end]
        
        return PaginatedReviewsType(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    def resolve_review_detail(self, info, review_id):
        try:
            review = ProfessionalReview.objects.get(id=review_id)
            return review
        except ConsultationReview.DoesNotExist:
            raise Exception("Review not found")

    def resolve_professional_review_summary(self, info, professional_id):
        try:
            professional = ProfessionalProfile.objects.get(id=professional_id)
            summary, created = ProfessionalReviewSummary.objects.get_or_create(
                professional=professional
            )
            if created or summary.total_reviews == 0:
                summary.update_summary()
            return summary
        except ProfessionalProfile.DoesNotExist:
            raise Exception("Professional not found")

    def resolve_verified_professionals(self, info, page=1, page_size=10, area_of_expertise=None, 
                                     location=None, min_rating=None, search_text=None):
        """Get verified professionals for client browsing"""
        
        # Start with verified professionals only
        professionals = ProfessionalProfile.objects.filter(
            verification_status='VERIFIED'
        ).select_related('user').prefetch_related('review_summary', 'pricing')
        
        # Apply filters
        if area_of_expertise:
            professionals = professionals.filter(area_of_expertise=area_of_expertise.upper())
        
        if location:
            professionals = professionals.filter(location__icontains=location)
        
        if search_text:
            # Search in user name, bio, and area of expertise
            professionals = professionals.filter(
                Q(user__first_name__icontains=search_text) |
                Q(user__last_name__icontains=search_text) |
                Q(bio_introduction__icontains=search_text) |
                Q(area_of_expertise__icontains=search_text)
            )
        
        if min_rating:
            # Filter by minimum average rating
            professionals = professionals.filter(
                review_summary__average_rating__gte=min_rating
            )
        
        # Order by rating (highest first), then by created date (newest first)
        professionals = professionals.order_by('-review_summary__average_rating', '-created_at')
        
        # Pagination
        total = professionals.count()
        start = (page - 1) * page_size
        end = start + page_size
        professionals = professionals[start:end]
        
        return PaginatedProfessionalsType(
            items=professionals,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
