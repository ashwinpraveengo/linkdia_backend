import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from core.models import (
    ConsultationBooking, ConsultationSlot, ProfessionalReview, 
    ProfessionalReviewSummary, ProfessionalProfile, CustomUser
)
from core.utils.permissions import login_required
from core.queries.booking_queries import (
    ConsultationBookingType, ProfessionalReviewType, 
    ConsultationSlotType, ProfessionalReviewSummaryType
)


class CreateBookingInput(graphene.InputObjectType):
    professional_id = graphene.UUID(required=True)
    slot_id = graphene.UUID(required=True)
    booking_date = graphene.Date(required=True)  # Specific date for the booking
    consultation_type = graphene.String(required=True)  
    problem_description = graphene.String()
    contact_preference = graphene.String()


class CancelBookingInput(graphene.InputObjectType):
    booking_id = graphene.UUID(required=True)
    cancellation_reason = graphene.String()


class CreateReviewInput(graphene.InputObjectType):
    professional_id = graphene.UUID(required=True)
    rating = graphene.Int(required=True)
    review_note = graphene.String()


class UpdateReviewInput(graphene.InputObjectType):
    review_id = graphene.UUID(required=True)
    rating = graphene.Int()
    review_note = graphene.String()


class CreateBookingMutation(graphene.Mutation):
    class Arguments:
        input = CreateBookingInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    booking = graphene.Field(ConsultationBookingType)

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        if not user.is_client:
            return CreateBookingMutation(
                success=False,
                message="Only clients can create bookings"
            )
        
        try:
            with transaction.atomic():
                # Get professional and slot
                try:
                    professional = ProfessionalProfile.objects.get(id=input.professional_id)
                    slot = ConsultationSlot.objects.select_for_update().get(
                        id=input.slot_id,
                        professional=professional
                    )
                except (ProfessionalProfile.DoesNotExist, ConsultationSlot.DoesNotExist):
                    return CreateBookingMutation(
                        success=False,
                        message="Professional or slot not found"
                    )
                
                # Validate booking date is not in the past
                from datetime import date
                if input.booking_date < date.today():
                    return CreateBookingMutation(
                        success=False,
                        message="Cannot book slots for past dates"
                    )
                
                # Check if the slot's date matches the requested booking date
                slot_date = slot.start_time.date()
                if slot_date != input.booking_date:
                    return CreateBookingMutation(
                        success=False,
                        message=f"This slot is for {slot_date}, but you requested {input.booking_date}"
                    )
                
                # Validate that the booking date/time is in the future
                from django.utils import timezone as django_timezone
                if slot.start_time <= django_timezone.now():
                    return CreateBookingMutation(
                        success=False,
                        message="Cannot book slots in the past"
                    )
                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            # Check if professional is verified
                if professional.verification_status != 'VERIFIED':
                    return CreateBookingMutation(
                        success=False,
                        message="Only verified professionals can be booked"
                    )
                
                # Check if slot is available
                if not slot.is_available():
                    return CreateBookingMutation(
                        success=False,
                        message="Selected time slot is not available"
                    )
                
                # Validate consultation type matches slot type
                if input.consultation_type != slot.consultation_type:
                    return CreateBookingMutation(
                        success=False,
                        message=f"This slot is only available for {slot.consultation_type.lower()} consultation"
                    )
                
                # Create booking using the slot's pre-calculated fee
                booking = ConsultationBooking.objects.create(
                    client=user,
                    professional=professional,
                    consultation_slot=slot,
                    consultation_type=input.consultation_type,
                    consultation_fee=slot.consultation_fee,  # Use slot's pre-calculated fee
                    client_problem_description=input.problem_description or "",
                    client_contact_preference=input.contact_preference or "",
                    booking_status='PENDING'
                )
                
                # Mark slot as booked
                slot.status = 'BOOKED'
                slot.save()
                
                return CreateBookingMutation(
                    success=True,
                    message="Booking created successfully",
                    booking=booking
                )
                
        except Exception as e:
            return CreateBookingMutation(
                success=False,
                message=f"Error creating booking: {str(e)}"
            )


class CancelBookingMutation(graphene.Mutation):
    class Arguments:
        input = CancelBookingInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    booking = graphene.Field(ConsultationBookingType)

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        try:
            booking = ConsultationBooking.objects.get(id=input.booking_id)
            
            # Check permission
            if booking.client != user and (not user.is_professional or booking.professional.user != user):
                return CancelBookingMutation(
                    success=False,
                    message="You don't have permission to cancel this booking"
                )
            
            # Cancel the booking
            success, message = booking.cancel_booking(
                cancelled_by_user=user,
                reason=input.cancellation_reason or ""
            )
            
            return CancelBookingMutation(
                success=success,
                message=message,
                booking=booking if success else None
            )
            
        except ConsultationBooking.DoesNotExist:
            return CancelBookingMutation(
                success=False,
                message="Booking not found"
            )
        except Exception as e:
            return CancelBookingMutation(
                success=False,
                message=f"Error cancelling booking: {str(e)}"
            )


class ConfirmBookingMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.UUID(required=True)
        meeting_link = graphene.String()
        meeting_id = graphene.String()
        meeting_password = graphene.String()
        consultation_address = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    booking = graphene.Field(ConsultationBookingType)

    @login_required
    def mutate(self, info, booking_id, meeting_link=None, meeting_id=None, 
               meeting_password=None, consultation_address=None):
        user = info.context.user
        
        if not user.is_professional:
            return ConfirmBookingMutation(
                success=False,
                message="Only professionals can confirm bookings"
            )
        
        try:
            booking = ConsultationBooking.objects.get(
                id=booking_id,
                professional__user=user
            )
            
            if booking.booking_status != 'PENDING':
                return ConfirmBookingMutation(
                    success=False,
                    message="Only pending bookings can be confirmed"
                )
            
            # Update booking details
            booking.booking_status = 'CONFIRMED'
            booking.confirmed_at = timezone.now()
            
            # Add meeting details for online consultations
            if booking.consultation_type == 'ONLINE':
                booking.meeting_link = meeting_link
                booking.meeting_id = meeting_id
                booking.meeting_password = meeting_password
            
            # Add address for offline consultations
            if booking.consultation_type == 'OFFLINE':
                booking.consultation_address = consultation_address
            
            booking.save()
            
            return ConfirmBookingMutation(
                success=True,
                message="Booking confirmed successfully",
                booking=booking
            )
            
        except ConsultationBooking.DoesNotExist:
            return ConfirmBookingMutation(
                success=False,
                message="Booking not found"
            )
        except Exception as e:
            return ConfirmBookingMutation(
                success=False,
                message=f"Error confirming booking: {str(e)}"
            )


class CompleteBookingMutation(graphene.Mutation):
    class Arguments:
        booking_id = graphene.UUID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    booking = graphene.Field(ConsultationBookingType)

    @login_required
    def mutate(self, info, booking_id):
        user = info.context.user
        
        if not user.is_professional:
            return CompleteBookingMutation(
                success=False,
                message="Only professionals can mark bookings as completed"
            )
        
        try:
            booking = ConsultationBooking.objects.get(
                id=booking_id,
                professional__user=user
            )
            
            if booking.booking_status != 'CONFIRMED':
                return CompleteBookingMutation(
                    success=False,
                    message="Only confirmed bookings can be completed"
                )
            
            booking.booking_status = 'COMPLETED'
            booking.completed_at = timezone.now()
            booking.save()
            
            return CompleteBookingMutation(
                success=True,
                message="Booking marked as completed",
                booking=booking
            )
            
        except ConsultationBooking.DoesNotExist:
            return CompleteBookingMutation(
                success=False,
                message="Booking not found"
            )
        except Exception as e:
            return CompleteBookingMutation(
                success=False,
                message=f"Error completing booking: {str(e)}"
            )


class CreateReviewMutation(graphene.Mutation):
    class Arguments:
        input = CreateReviewInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    review = graphene.Field(ProfessionalReviewType)

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        if not user.is_client:
            return CreateReviewMutation(
                success=False,
                message="Only clients can create reviews"
            )
        
        try:
            # Get professional
            try:
                professional = ProfessionalProfile.objects.get(id=input.professional_id)
            except ProfessionalProfile.DoesNotExist:
                return CreateReviewMutation(
                    success=False,
                    message="Professional not found"
                )
            
            # Check if review already exists
            if ProfessionalReview.objects.filter(client=user, professional=professional).exists():
                return CreateReviewMutation(
                    success=False,
                    message="You have already reviewed this professional"
                )
            
            # Validate rating
            if not 1 <= input.rating <= 5:
                return CreateReviewMutation(
                    success=False,
                    message="Rating must be between 1 and 5"
                )
            
            # Create review
            review = ProfessionalReview.objects.create(
                client=user,
                professional=professional,
                rating=input.rating,
                review_note=input.review_note or ""
            )
            
            # Update professional review summary
            summary, created = ProfessionalReviewSummary.objects.get_or_create(
                professional=professional
            )
            summary.update_summary()
            
            return CreateReviewMutation(
                success=True,
                message="Review created successfully",
                review=review
            )
            
        except ConsultationBooking.DoesNotExist:
            return CreateReviewMutation(
                success=False,
                message="Booking not found"
            )
        except Exception as e:
            return CreateReviewMutation(
                success=False,
                message=f"Error creating review: {str(e)}"
            )


class UpdateReviewMutation(graphene.Mutation):
    class Arguments:
        input = UpdateReviewInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    review = graphene.Field(ProfessionalReviewType)

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        try:
            review = ProfessionalReview.objects.get(
                id=input.review_id,
                client=user
            )
            
            # Update fields if provided
            if input.rating is not None:
                if not 1 <= input.rating <= 5:
                    return UpdateReviewMutation(
                        success=False,
                        message="Rating must be between 1 and 5"
                    )
                review.rating = input.rating
            
            if input.review_note is not None:
                review.review_note = input.review_note
            
            review.save()
            
            # Update professional review summary
            summary, created = ProfessionalReviewSummary.objects.get_or_create(
                professional=review.professional
            )
            summary.update_summary()
            
            return UpdateReviewMutation(
                success=True,
                message="Review updated successfully",
                review=review
            )
            
        except ProfessionalReview.DoesNotExist:
            return UpdateReviewMutation(
                success=False,
                message="Review not found"
            )
        except Exception as e:
            return UpdateReviewMutation(
                success=False,
                message=f"Error updating review: {str(e)}"
            )


class BookingMutations(graphene.ObjectType):
    create_booking = CreateBookingMutation.Field()
    cancel_booking = CancelBookingMutation.Field()
    confirm_booking = ConfirmBookingMutation.Field()
    complete_booking = CompleteBookingMutation.Field()
    create_review = CreateReviewMutation.Field()
    update_review = UpdateReviewMutation.Field()
