import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.db.models import Q, Avg, Count
from datetime import datetime, timedelta

from core.models import (
    CustomUser, ProfessionalProfile, ConsultationBooking, 
    BookingHistory, ConsultationReview, ConsultationSlot,
    ConsultationAvailability, Notification
)
from core.mutations.booking_mutations import (
    ConsultationBookingType, BookingHistoryType, ConsultationReviewType,
    ConsultationSlotType, ConsultationAvailabilityType
)


class ProfessionalStatsType(graphene.ObjectType):
    total_bookings = graphene.Int()
    completed_consultations = graphene.Int()
    average_rating = graphene.Float()
    total_reviews = graphene.Int()
    earnings_this_month = graphene.Float()
    upcoming_bookings = graphene.Int()


class ClientStatsType(graphene.ObjectType):
    total_bookings = graphene.Int()
    completed_consultations = graphene.Int()
    upcoming_bookings = graphene.Int()
    total_spent = graphene.Float()
    pending_reviews = graphene.Int()


class BookingQuery(graphene.ObjectType):
    # Booking queries
    my_bookings = graphene.List(
        ConsultationBookingType,
        status=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    booking = graphene.Field(
        ConsultationBookingType,
        id=graphene.ID(required=True)
    )
    
    booking_history = graphene.List(
        BookingHistoryType,
        booking_id=graphene.ID(required=True)
    )
    
    # Professional queries
    professional_bookings = graphene.List(
        ConsultationBookingType,
        status=graphene.String(),
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    professional_availability = graphene.Field(ConsultationAvailabilityType)
    
    professional_stats = graphene.Field(ProfessionalStatsType)
    
    professional_time_slots = graphene.List(
        ConsultationSlotType,
        date_from=graphene.Date(),
        date_to=graphene.Date(),
        status=graphene.String()
    )
    
    # Client queries
    client_stats = graphene.Field(ClientStatsType)
    
    # Review queries
    professional_reviews = graphene.List(
        ConsultationReviewType,
        professional_id=graphene.ID(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    my_reviews = graphene.List(ConsultationReviewType)
    
    # Search and discovery
    available_professionals = graphene.List(
        'core.mutations.auth_mutations.ProfessionalProfileType',
        expertise_area=graphene.String(),
        location=graphene.String(),
        min_rating=graphene.Float(),
        available_date=graphene.Date(),
        consultation_type=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    available_time_slots = graphene.List(
        ConsultationSlotType,
        professional_id=graphene.ID(required=True),
        date=graphene.Date(required=True)
    )

    def resolve_my_bookings(self, info, status=None, limit=None, offset=None):
        user = info.context.user
        if not user.is_authenticated:
            return []

        bookings = ConsultationBooking.objects.filter(
            Q(client=user) | Q(professional__user=user)
        ).order_by('-consultation_date')

        if status:
            bookings = bookings.filter(status=status)
        
        if offset:
            bookings = bookings[offset:]
        
        if limit:
            bookings = bookings[:limit]

        return bookings

    def resolve_booking(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return None

        try:
            booking = ConsultationBooking.objects.get(id=id)
            # Check if user has access to this booking
            if booking.client == user or booking.professional.user == user:
                return booking
        except ConsultationBooking.DoesNotExist:
            pass
        
        return None

    def resolve_booking_history(self, info, booking_id):
        user = info.context.user
        if not user.is_authenticated:
            return []

        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            # Check if user has access to this booking
            if booking.client == user or booking.professional.user == user:
                return booking.history.all()
        except ConsultationBooking.DoesNotExist:
            pass
        
        return []

    def resolve_professional_bookings(self, info, status=None, date_from=None, 
                                    date_to=None, limit=None, offset=None):
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return []

        try:
            professional = user.professional_profile
            bookings = ConsultationBooking.objects.filter(
                professional=professional
            ).order_by('-consultation_date')

            if status:
                bookings = bookings.filter(status=status)
            
            if date_from:
                bookings = bookings.filter(consultation_date__date__gte=date_from)
            
            if date_to:
                bookings = bookings.filter(consultation_date__date__lte=date_to)
            
            if offset:
                bookings = bookings[offset:]
            
            if limit:
                bookings = bookings[:limit]

            return bookings
        except:
            return []

    def resolve_professional_availability(self, info):
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return None

        try:
            professional = user.professional_profile
            return professional.availability.filter(is_active=True).first()
        except:
            return None

    def resolve_professional_stats(self, info):
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return None

        try:
            professional = user.professional_profile
            
            # Calculate stats
            total_bookings = ConsultationBooking.objects.filter(professional=professional).count()
            completed_consultations = ConsultationBooking.objects.filter(
                professional=professional, 
                status='COMPLETED'
            ).count()
            
            upcoming_bookings = ConsultationBooking.objects.filter(
                professional=professional,
                status='CONFIRMED',
                consultation_date__gt=timezone.now()
            ).count()
            
            # Calculate earnings this month
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            earnings_this_month = ConsultationBooking.objects.filter(
                professional=professional,
                status='COMPLETED',
                completed_at__gte=current_month,
                payment_status='PAID'
            ).aggregate(total=models.Sum('final_amount'))['total'] or 0.0

            return ProfessionalStatsType(
                total_bookings=total_bookings,
                completed_consultations=completed_consultations,
                average_rating=float(professional.average_rating),
                total_reviews=professional.total_reviews,
                earnings_this_month=float(earnings_this_month),
                upcoming_bookings=upcoming_bookings
            )
        except:
            return None

    def resolve_professional_time_slots(self, info, date_from=None, date_to=None, status=None):
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            return []

        try:
            professional = user.professional_profile
            slots = ConsultationSlot.objects.filter(professional=professional)

            if date_from:
                slots = slots.filter(start_time__date__gte=date_from)
            
            if date_to:
                slots = slots.filter(start_time__date__lte=date_to)
            
            if status:
                slots = slots.filter(status=status)

            return slots.order_by('start_time')
        except:
            return []

    def resolve_client_stats(self, info):
        user = info.context.user
        if not user.is_authenticated or not user.is_client:
            return None

        try:
            total_bookings = ConsultationBooking.objects.filter(client=user).count()
            completed_consultations = ConsultationBooking.objects.filter(
                client=user, 
                status='COMPLETED'
            ).count()
            
            upcoming_bookings = ConsultationBooking.objects.filter(
                client=user,
                status='CONFIRMED',
                consultation_date__gt=timezone.now()
            ).count()
            
            # Calculate total spent
            total_spent = ConsultationBooking.objects.filter(
                client=user,
                payment_status='PAID'
            ).aggregate(total=models.Sum('final_amount'))['total'] or 0.0

            # Pending reviews
            pending_reviews = ConsultationBooking.objects.filter(
                client=user,
                status='COMPLETED'
            ).exclude(
                id__in=ConsultationReview.objects.filter(client=user).values_list('booking_id', flat=True)
            ).count()

            return ClientStatsType(
                total_bookings=total_bookings,
                completed_consultations=completed_consultations,
                upcoming_bookings=upcoming_bookings,
                total_spent=float(total_spent),
                pending_reviews=pending_reviews
            )
        except:
            return None

    def resolve_professional_reviews(self, info, professional_id=None, limit=None, offset=None):
        if professional_id:
            reviews = ConsultationReview.objects.filter(
                professional_id=professional_id,
                is_published=True
            ).order_by('-created_at')
        else:
            reviews = ConsultationReview.objects.filter(
                is_published=True
            ).order_by('-created_at')
        
        if offset:
            reviews = reviews[offset:]
        
        if limit:
            reviews = reviews[:limit]

        return reviews

    def resolve_my_reviews(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []

        if user.is_client:
            return ConsultationReview.objects.filter(client=user).order_by('-created_at')
        elif user.is_professional:
            try:
                professional = user.professional_profile
                return ConsultationReview.objects.filter(
                    professional=professional
                ).order_by('-created_at')
            except:
                return []
        
        return []

    def resolve_available_professionals(self, info, expertise_area=None, location=None, 
                                      min_rating=None, available_date=None, 
                                      consultation_type=None, limit=None, offset=None):
        from core.models import ProfessionalProfile
        
        professionals = ProfessionalProfile.objects.filter(
            verification_status='VERIFIED',
            onboarding_completed=True,
            is_available=True
        )

        if expertise_area:
            professionals = professionals.filter(area_of_expertise=expertise_area)
        
        if location:
            professionals = professionals.filter(location__icontains=location)
        
        if min_rating:
            professionals = professionals.filter(average_rating__gte=min_rating)
        
        if available_date:
            # Check if professional has availability on the given date
            # This is a simplified check - in real implementation, you'd check actual time slots
            day_of_week = available_date.strftime('%A').lower()
            availability_filter = {f'availability__{day_of_week}': True}
            professionals = professionals.filter(**availability_filter)
        
        if consultation_type:
            professionals = professionals.filter(
                Q(availability__consultation_type=consultation_type) |
                Q(availability__consultation_type='BOTH')
            )

        professionals = professionals.distinct().order_by('-average_rating', '-total_reviews')
        
        if offset:
            professionals = professionals[offset:]
        
        if limit:
            professionals = professionals[:limit]

        return professionals

    def resolve_available_time_slots(self, info, professional_id, date):
        try:
            professional = ProfessionalProfile.objects.get(id=professional_id)
            
            # Get available slots for the given date
            slots = ConsultationSlot.objects.filter(
                professional=professional,
                start_time__date=date,
                status='AVAILABLE'
            ).order_by('start_time')

            return slots
        except ProfessionalProfile.DoesNotExist:
            return []


# Import fix for models
from django.db import models
