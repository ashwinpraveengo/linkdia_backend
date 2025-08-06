import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import uuid

from core.models import (
    CustomUser, ProfessionalProfile, ConsultationBooking, 
    BookingHistory, ConsultationReview, ConsultationSlot,
    ConsultationAvailability, Notification, NotificationTemplate
)


# GraphQL Types
class ConsultationBookingType(DjangoObjectType):
    client_name = graphene.String()
    professional_name = graphene.String()
    is_upcoming = graphene.Boolean()
    is_past = graphene.Boolean()
    can_cancel = graphene.Boolean()
    
    class Meta:
        model = ConsultationBooking
        fields = '__all__'
    
    def resolve_client_name(self, info):
        return self.client.full_name
    
    def resolve_professional_name(self, info):
        return self.professional.user.full_name
    
    def resolve_is_upcoming(self, info):
        return self.is_upcoming
    
    def resolve_is_past(self, info):
        return self.is_past
    
    def resolve_can_cancel(self, info):
        return self.can_cancel()


class BookingHistoryType(DjangoObjectType):
    class Meta:
        model = BookingHistory
        fields = '__all__'


class ConsultationReviewType(DjangoObjectType):
    class Meta:
        model = ConsultationReview
        fields = '__all__'


class ConsultationSlotType(DjangoObjectType):
    is_available = graphene.Boolean()
    
    class Meta:
        model = ConsultationSlot
        fields = '__all__'
    
    def resolve_is_available(self, info):
        return self.is_available()


class ConsultationAvailabilityType(DjangoObjectType):
    available_days = graphene.List(graphene.String)
    
    class Meta:
        model = ConsultationAvailability
        fields = '__all__'
    
    def resolve_available_days(self, info):
        return self.get_available_days()


# Payload Types
class BookingPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    booking = graphene.Field(ConsultationBookingType)
    errors = graphene.List(graphene.String)


class SlotPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    slot = graphene.Field(ConsultationSlotType)
    errors = graphene.List(graphene.String)


class ReviewPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    review = graphene.Field(ConsultationReviewType)
    errors = graphene.List(graphene.String)


# Mutations
class CreateBookingMutation(graphene.Mutation):
    class Arguments:
        professional_id = graphene.ID(required=True)
        consultation_date = graphene.DateTime(required=True)
        duration_minutes = graphene.Int(required=True)
        consultation_type = graphene.String(required=True)
        case_description = graphene.String(required=True)
        client_notes = graphene.String()
        urgency_level = graphene.String()
        location_address = graphene.String()

    Output = BookingPayload

    def mutate(self, info, professional_id, consultation_date, duration_minutes, 
               consultation_type, case_description, client_notes="", urgency_level="MEDIUM",
               location_address=""):
        
        user = info.context.user
        if not user.is_authenticated:
            return BookingPayload(
                success=False,
                message="Authentication required",
                errors=["User must be logged in to create bookings"]
            )

        if not user.is_client:
            return BookingPayload(
                success=False,
                message="Only clients can create bookings",
                errors=["User must be a client to create bookings"]
            )

        try:
            # Get professional
            professional = ProfessionalProfile.objects.get(id=professional_id)
            
            # Validate consultation type
            if consultation_type not in ['ONLINE', 'OFFLINE']:
                return BookingPayload(
                    success=False,
                    message="Invalid consultation type",
                    errors=["Consultation type must be ONLINE or OFFLINE"]
                )

            # Check if professional is available at the requested time
            # This is a simplified check - in real implementation, you'd check against availability slots
            if consultation_date <= timezone.now():
                return BookingPayload(
                    success=False,
                    message="Cannot book consultation in the past",
                    errors=["Consultation date must be in the future"]
                )

            # Get professional's availability settings
            try:
                availability = professional.availability.get(is_active=True)
                hourly_rate = availability.hourly_rate
            except ConsultationAvailability.DoesNotExist:
                return BookingPayload(
                    success=False,
                    message="Professional has not set availability",
                    errors=["Professional is not available for bookings"]
                )

            # Calculate pricing
            total_amount = (hourly_rate * duration_minutes) / 60
            
            # Create booking
            booking = ConsultationBooking.objects.create(
                client=user,
                professional=professional,
                consultation_date=consultation_date,
                duration_minutes=duration_minutes,
                consultation_type=consultation_type,
                case_description=case_description,
                client_notes=client_notes,
                urgency_level=urgency_level,
                location_address=location_address if consultation_type == 'OFFLINE' else '',
                hourly_rate=hourly_rate,
                total_amount=total_amount,
                final_amount=total_amount,
                status='PENDING'
            )

            # Create booking history entry
            BookingHistory.objects.create(
                booking=booking,
                action='CREATED',
                performed_by=user,
                description=f"Booking created by {user.full_name}"
            )

            # Send notification to professional (if auto-accept is enabled)
            if hasattr(professional, 'settings') and professional.settings.auto_accept_bookings:
                booking.status = 'CONFIRMED'
                booking.confirmed_at = timezone.now()
                booking.confirmed_by = professional.user
                booking.save()
                
                BookingHistory.objects.create(
                    booking=booking,
                    action='CONFIRMED',
                    performed_by=professional.user,
                    description="Booking auto-confirmed"
                )

            return BookingPayload(
                success=True,
                message="Booking created successfully",
                booking=booking
            )

        except ProfessionalProfile.DoesNotExist:
            return BookingPayload(
                success=False,
                message="Professional not found",
                errors=["The specified professional does not exist"]
            )
        except Exception as e:
            return BookingPayload(
                success=False,
                message="An error occurred while creating the booking",
                errors=[str(e)]
            )


class ConfirmBookingMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.ID(required=True)
        meeting_link = graphene.String()
        meeting_id = graphene.String()
        meeting_password = graphene.String()

    Output = BookingPayload

    def mutate(self, info, booking_id, meeting_link="", meeting_id="", meeting_password=""):
        user = info.context.user
        if not user.is_authenticated:
            return BookingPayload(
                success=False,
                message="Authentication required",
                errors=["User must be logged in"]
            )

        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            
            # Check if user is the professional
            if booking.professional.user != user:
                return BookingPayload(
                    success=False,
                    message="Unauthorized",
                    errors=["Only the assigned professional can confirm this booking"]
                )

            if booking.status != 'PENDING':
                return BookingPayload(
                    success=False,
                    message="Booking cannot be confirmed",
                    errors=[f"Booking is already {booking.status.lower()}"]
                )

            # Update booking
            booking.status = 'CONFIRMED'
            booking.confirmed_at = timezone.now()
            booking.confirmed_by = user
            
            if booking.consultation_type == 'ONLINE':
                booking.meeting_link = meeting_link
                booking.meeting_id = meeting_id
                booking.meeting_password = meeting_password
            
            booking.save()

            # Create history entry
            BookingHistory.objects.create(
                booking=booking,
                action='CONFIRMED',
                performed_by=user,
                description=f"Booking confirmed by {user.full_name}"
            )

            return BookingPayload(
                success=True,
                message="Booking confirmed successfully",
                booking=booking
            )

        except ConsultationBooking.DoesNotExist:
            return BookingPayload(
                success=False,
                message="Booking not found",
                errors=["The specified booking does not exist"]
            )


class CancelBookingMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.ID(required=True)
        cancellation_reason = graphene.String(required=True)

    Output = BookingPayload

    def mutate(self, info, booking_id, cancellation_reason):
        user = info.context.user
        if not user.is_authenticated:
            return BookingPayload(
                success=False,
                message="Authentication required",
                errors=["User must be logged in"]
            )

        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            
            # Check if user can cancel this booking
            if booking.client != user and booking.professional.user != user:
                return BookingPayload(
                    success=False,
                    message="Unauthorized",
                    errors=["You can only cancel your own bookings"]
                )

            if booking.status in ['CANCELLED_BY_CLIENT', 'CANCELLED_BY_PROFESSIONAL', 'COMPLETED']:
                return BookingPayload(
                    success=False,
                    message="Booking cannot be cancelled",
                    errors=[f"Booking is already {booking.status.lower()}"]
                )

            # Calculate cancellation fee
            cancellation_fee = booking.get_cancellation_fee()
            
            # Update booking
            if booking.client == user:
                booking.status = 'CANCELLED_BY_CLIENT'
            else:
                booking.status = 'CANCELLED_BY_PROFESSIONAL'
            
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = cancellation_reason
            booking.cancellation_fee = cancellation_fee
            booking.save()

            # Create history entry
            action = 'CANCELLED'
            description = f"Booking cancelled by {user.full_name}. Reason: {cancellation_reason}"
            
            BookingHistory.objects.create(
                booking=booking,
                action=action,
                performed_by=user,
                description=description
            )

            return BookingPayload(
                success=True,
                message="Booking cancelled successfully",
                booking=booking
            )

        except ConsultationBooking.DoesNotExist:
            return BookingPayload(
                success=False,
                message="Booking not found",
                errors=["The specified booking does not exist"]
            )


class CompleteBookingMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.ID(required=True)
        professional_notes = graphene.String()
        follow_up_required = graphene.Boolean()
        follow_up_notes = graphene.String()

    Output = BookingPayload

    def mutate(self, info, booking_id, professional_notes="", follow_up_required=False, follow_up_notes=""):
        user = info.context.user
        if not user.is_authenticated:
            return BookingPayload(
                success=False,
                message="Authentication required",
                errors=["User must be logged in"]
            )

        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            
            # Check if user is the professional
            if booking.professional.user != user:
                return BookingPayload(
                    success=False,
                    message="Unauthorized",
                    errors=["Only the assigned professional can complete this booking"]
                )

            if booking.status != 'CONFIRMED':
                return BookingPayload(
                    success=False,
                    message="Booking cannot be completed",
                    errors=["Only confirmed bookings can be completed"]
                )

            # Update booking
            booking.status = 'COMPLETED'
            booking.completed_at = timezone.now()
            booking.professional_notes = professional_notes
            booking.follow_up_required = follow_up_required
            booking.follow_up_notes = follow_up_notes
            booking.save()

            # Update professional's total consultations
            booking.professional.total_consultations += 1
            booking.professional.save()

            # Create history entry
            BookingHistory.objects.create(
                booking=booking,
                action='COMPLETED',
                performed_by=user,
                description=f"Consultation completed by {user.full_name}"
            )

            return BookingPayload(
                success=True,
                message="Booking completed successfully",
                booking=booking
            )

        except ConsultationBooking.DoesNotExist:
            return BookingPayload(
                success=False,
                message="Booking not found",
                errors=["The specified booking does not exist"]
            )


class CreateReviewMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.ID(required=True)
        rating = graphene.Int(required=True)
        review_text = graphene.String(required=True)
        communication_rating = graphene.Int()
        expertise_rating = graphene.Int()
        professionalism_rating = graphene.Int()
        value_for_money_rating = graphene.Int()
        would_recommend = graphene.Boolean()
        tags = graphene.String()

    Output = ReviewPayload

    def mutate(self, info, booking_id, rating, review_text, 
               communication_rating=None, expertise_rating=None, 
               professionalism_rating=None, value_for_money_rating=None,
               would_recommend=True, tags=""):
        
        user = info.context.user
        if not user.is_authenticated:
            return ReviewPayload(
                success=False,
                message="Authentication required",
                errors=["User must be logged in"]
            )

        try:
            booking = ConsultationBooking.objects.get(id=booking_id)
            
            # Check if user is the client
            if booking.client != user:
                return ReviewPayload(
                    success=False,
                    message="Unauthorized",
                    errors=["Only the client can review this booking"]
                )

            if booking.status != 'COMPLETED':
                return ReviewPayload(
                    success=False,
                    message="Cannot review incomplete booking",
                    errors=["Only completed bookings can be reviewed"]
                )

            # Check if review already exists
            if hasattr(booking, 'review'):
                return ReviewPayload(
                    success=False,
                    message="Review already exists",
                    errors=["This booking has already been reviewed"]
                )

            # Validate rating
            if rating < 1 or rating > 5:
                return ReviewPayload(
                    success=False,
                    message="Invalid rating",
                    errors=["Rating must be between 1 and 5"]
                )

            # Create review
            review = ConsultationReview.objects.create(
                booking=booking,
                client=user,
                professional=booking.professional,
                rating=rating,
                review_text=review_text,
                communication_rating=communication_rating,
                expertise_rating=expertise_rating,
                professionalism_rating=professionalism_rating,
                value_for_money_rating=value_for_money_rating,
                would_recommend=would_recommend,
                tags=tags
            )

            return ReviewPayload(
                success=True,
                message="Review created successfully",
                review=review
            )

        except ConsultationBooking.DoesNotExist:
            return ReviewPayload(
                success=False,
                message="Booking not found",
                errors=["The specified booking does not exist"]
            )


class SetAvailabilityMutation(graphene.Mutation):
    class Arguments:
        monday = graphene.Boolean()
        tuesday = graphene.Boolean()
        wednesday = graphene.Boolean()
        thursday = graphene.Boolean()
        friday = graphene.Boolean()
        saturday = graphene.Boolean()
        sunday = graphene.Boolean()
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        consultation_type = graphene.String(required=True)
        default_duration_minutes = graphene.Int(required=True)
        hourly_rate = graphene.Float(required=True)
        buffer_time_minutes = graphene.Int()
        max_sessions_per_day = graphene.Int()

    Output = ConsultationAvailabilityType

    def mutate(self, info, start_time, end_time, consultation_type, 
               default_duration_minutes, hourly_rate, monday=False, tuesday=False,
               wednesday=False, thursday=False, friday=False, saturday=False,
               sunday=False, buffer_time_minutes=15, max_sessions_per_day=None):
        
        user = info.context.user
        if not user.is_authenticated or not user.is_professional:
            raise Exception("Only professionals can set availability")

        try:
            professional = user.professional_profile
            
            # Get or create availability
            availability, created = ConsultationAvailability.objects.get_or_create(
                professional=professional,
                defaults={
                    'monday': monday,
                    'tuesday': tuesday,
                    'wednesday': wednesday,
                    'thursday': thursday,
                    'friday': friday,
                    'saturday': saturday,
                    'sunday': sunday,
                    'start_time': start_time,
                    'end_time': end_time,
                    'consultation_type': consultation_type,
                    'default_duration_minutes': default_duration_minutes,
                    'hourly_rate': hourly_rate,
                    'buffer_time_minutes': buffer_time_minutes,
                    'max_sessions_per_day': max_sessions_per_day,
                    'is_active': True
                }
            )

            if not created:
                # Update existing availability
                availability.monday = monday
                availability.tuesday = tuesday
                availability.wednesday = wednesday
                availability.thursday = thursday
                availability.friday = friday
                availability.saturday = saturday
                availability.sunday = sunday
                availability.start_time = start_time
                availability.end_time = end_time
                availability.consultation_type = consultation_type
                availability.default_duration_minutes = default_duration_minutes
                availability.hourly_rate = hourly_rate
                availability.buffer_time_minutes = buffer_time_minutes
                availability.max_sessions_per_day = max_sessions_per_day
                availability.save()

            return availability

        except Exception as e:
            raise Exception(f"Error setting availability: {str(e)}")


# Main Mutation Class
class BookingMutations(graphene.ObjectType):
    create_booking = CreateBookingMutation.Field()
    confirm_booking = ConfirmBookingMutation.Field()
    cancel_booking = CancelBookingMutation.Field()
    complete_booking = CompleteBookingMutation.Field()
    create_review = CreateReviewMutation.Field()
    set_availability = SetAvailabilityMutation.Field()
