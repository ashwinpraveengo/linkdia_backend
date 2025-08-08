from typing import Dict, List, Optional
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from core.models import (
    CustomUser,
    # NotificationTemplate,  # Commented out until implemented
    # Notification,  # Commented out until implemented
    ProfessionalProfile
)
import logging
from celery import shared_task 

logger = logging.getLogger(__name__)


def send_welcome_email(user: CustomUser) -> bool:
    """
    Send welcome email to new user
    
    Args:
        user: New user instance
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        context = {
            'user': user,
            'user_type': user.get_user_type_display(),
            'login_url': f"{settings.FRONTEND_URL}/login",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard"
        }
        
        if user.is_professional:
            subject = "Welcome to LinkDia - Start Your Professional Journey"
            template = 'emails/welcome_professional.html'
        else:
            subject = "Welcome to LinkDia - Find Legal Experts"
            template = 'emails/welcome_client.html'
        
        return send_email_notification(
            recipient=user,
            subject=subject,
            template=template,
            context=context
        )
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user.id}: {str(e)}")
        return False


def send_verification_email(user: CustomUser, verification_link: str) -> bool:
    """
    Send email verification link
    
    Args:
        user: User instance
        verification_link: Email verification link
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        context = {
            'user': user,
            'verification_link': verification_link,
            'support_email': settings.SUPPORT_EMAIL
        }
        
        subject = "Verify Your Email Address - LinkDia"
        template = 'emails/email_verification.html'
        
        return send_email_notification(
            recipient=user,
            subject=subject,
            template=template,
            context=context
        )
        
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user.id}: {str(e)}")
        return False


def send_kyc_completion_notice(professional: ProfessionalProfile, approved: bool) -> bool:
    """
    Send KYC completion notice to professional
    
    Args:
        professional: Professional profile instance
        approved: Whether KYC was approved
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        context = {
            'professional': professional,
            'user': professional.user,
            'approved': approved,
            'dashboard_url': f"{settings.FRONTEND_URL}/professional/dashboard"
        }
        
        if approved:
            subject = "KYC Approved - You're Ready to Start"
            template = 'emails/kyc_approved.html'
        else:
            subject = "KYC Review Required - Additional Information Needed"
            template = 'emails/kyc_rejected.html'
        
        return send_email_notification(
            recipient=professional.user,
            subject=subject,
            template=template,
            context=context
        )
        
    except Exception as e:
        logger.error(f"Failed to send KYC notice to professional {professional.id}: {str(e)}")
        return False


def send_email_notification(
    recipient: CustomUser,
    subject: str,
    template: str,
    context: Dict,
    from_email: Optional[str] = None
) -> bool:
    """
    Send email notification using template
    
    Args:
        recipient: User to send email to
        subject: Email subject
        template: Template path
        context: Template context
        from_email: From email address
    
    Returns:
        bool: True if email was sent successfully
    """
    try:
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Render HTML content
        html_content = render_to_string(template, context)
        
        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body='',  # Plain text fallback
            from_email=from_email,
            to=[recipient.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Log notification in database
        create_notification_record(
            recipient=recipient,
            subject=subject,
            content=html_content,
            channel='EMAIL',
            status='SENT'
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
        
        # Log failed notification
        create_notification_record(
            recipient=recipient,
            subject=subject,
            content=f"Failed to send: {str(e)}",
            channel='EMAIL',
            status='FAILED'
        )
        
        return False


def create_notification_record(
    recipient: CustomUser,
    subject: str,
    content: str,
    channel: str = 'EMAIL',
    status: str = 'PENDING',
    metadata: Optional[Dict] = None
) -> None:  # Changed return type since Notification model doesn't exist yet
    """
    Create notification record in database
    
    Args:
        recipient: User receiving notification
        subject: Notification subject
        content: Notification content
        channel: Notification channel
        status: Notification status
        metadata: Additional metadata (optional)
    
    Returns:
        None: Placeholder until Notification model is implemented
    """
    # TODO: Implement when Notification model is created
    # try:
    #     notification = Notification.objects.create(
    #         recipient=recipient,
    #         subject=subject,
    #         content=content,
    #         status=status,
    #         booking=booking,
    #         metadata=metadata or {}
    #     )
    #     
    #     if status == 'SENT':
    #         notification.sent_at = timezone.now()
    #         notification.save()
    #     
    #     return notification
    #     
    # except Exception as e:
    #     logger.error(f"Failed to create notification record: {str(e)}")
    #     raise
    
    # For now, just log that a notification would be created
    logger.info(f"Would create notification for {recipient.email}: {subject}")
    return None


def queue_notification(
    recipient_id: str,
    notification_type: str,
    context: Dict,
    schedule_at: Optional[timezone.datetime] = None
) -> bool:
    """
    Queue notification for later processing (use with Celery)
    
    Args:
        recipient_id: ID of recipient user
        notification_type: Type of notification
        context: Notification context
        schedule_at: When to send the notification
    
    Returns:
        bool: True if notification was queued successfully
    """
    try:
        # If using Celery, queue the task
        if schedule_at:
            # Schedule for specific time
            process_notification.apply_async(
                args=[recipient_id, notification_type, context],
                eta=schedule_at
            )
        else:
            # Process immediately (asynchronously)
            process_notification.delay(recipient_id, notification_type, context)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue notification: {str(e)}")
        return False


@shared_task
def process_notification_queue(recipient_id: str, notification_type: str, context: Dict):
    """
    Celery task to process queued notifications
    
    Args:
        recipient_id: ID of recipient user
        notification_type: Type of notification
        context: Notification context
    """
    try:
        recipient = CustomUser.objects.get(id=recipient_id)
        
        notification_handlers = {
            'BOOKING_CONFIRMATION': lambda: send_booking_confirmation(context['booking']),
            'BOOKING_REMINDER': lambda: send_booking_reminder(context['booking'], context.get('hours_before', 24)),
            'BOOKING_CANCELLATION': lambda: send_cancellation_notice(
                context['booking'], 
                context['cancelled_by'], 
                context.get('reason', '')
            ),
            'WELCOME_EMAIL': lambda: send_welcome_email(recipient),
            'EMAIL_VERIFICATION': lambda: send_verification_email(recipient, context['verification_link']),
            'KYC_COMPLETION': lambda: send_kyc_completion_notice(
                context['professional'], 
                context['approved']
            )
        }
        
        handler = notification_handlers.get(notification_type)
        if handler:
            handler()
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
            
    except CustomUser.DoesNotExist:
        logger.error(f"Recipient user {recipient_id} not found")
    except Exception as e:
        logger.error(f"Failed to process notification: {str(e)}")


def send_bulk_notifications(
    recipients: List[CustomUser],
    subject: str,
    template: str,
    context: Dict
) -> Dict[str, int]:
    """
    Send notifications to multiple recipients
    
    Args:
        recipients: List of recipient users
        subject: Email subject
        template: Template path
        context: Template context
    
    Returns:
        dict: Results with counts of successful/failed sends
    """
    results = {'successful': 0, 'failed': 0}
    
    for recipient in recipients:
        if send_email_notification(recipient, subject, template, context):
            results['successful'] += 1
        else:
            results['failed'] += 1
    
    return results
