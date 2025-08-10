from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('PROFESSIONAL', 'Professional'),
        ('CLIENT', 'Client'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    user_type = models.CharField(max_length=12, choices=USER_TYPE_CHOICES, default='CLIENT')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Profile picture stored as binary data
    profile_picture_data = models.BinaryField(blank=True, null=True)
    profile_picture_name = models.CharField(max_length=255, blank=True, null=True)
    profile_picture_content_type = models.CharField(max_length=100, blank=True, null=True)
    profile_picture_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    
    # Google OAuth fields
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    is_google_user = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_professional(self):
        return self.user_type == 'PROFESSIONAL'

    @property
    def is_client(self):
        return self.user_type == 'CLIENT'

    def get_profile(self):
        """Get the specific profile based on user type"""
        if self.is_professional:
            return getattr(self, 'professional_profile', None)
        elif self.is_client:
            return getattr(self, 'client_profile', None)
        return None


class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Password reset token for {self.user.email}"



class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_profiles'

    def __str__(self):
        return f"{self.user.full_name} - Client"

class ProfessionalProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_REVIEW', 'In Review'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    
    ONBOARDING_STATUS_CHOICES = [
        ('PROFILE_SETUP', 'Profile Setup'),
        ('DOCUMENT_UPLOAD', 'Document Upload'),
        ('VIDEO_KYC', 'Video KYC'),
        ('PORTFOLIO', 'Portfolio'),
        ('CONSULTATION_HOURS', 'Consultation Hours'),
        ('PAYMENT_SETUP', 'Payment Setup'),
        ('COMPLETED', 'Completed'),
    ]

    EXPERTISE_AREA_CHOICES = [
        ('CRIMINAL_LAWYER', 'Criminal Lawyer'),
        ('CORPORATE_LAWYER', 'Corporate Lawyer'),
        ('FAMILY_LAWYER', 'Family Lawyer'),
        ('REAL_ESTATE_LAWYER', 'Real Estate Lawyer'),
        ('IMMIGRATION_LAWYER', 'Immigration Lawyer'),
        ('PERSONAL_INJURY_LAWYER', 'Personal Injury Lawyer'),
        ('INTELLECTUAL_PROPERTY_LAWYER', 'Intellectual Property Lawyer'),
        ('TAX_LAWYER', 'Tax Lawyer'),
        ('EMPLOYMENT_LAWYER', 'Employment Lawyer'),
        ('ENVIRONMENTAL_LAWYER', 'Environmental Lawyer'),
        ('OTHER', 'Other'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='professional_profile')  
    
    # Step 1: Profile Setup Fields - only essential fields
    area_of_expertise = models.CharField(max_length=50, choices=EXPERTISE_AREA_CHOICES, blank=True)
    years_of_experience = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        help_text="e.g., '1-3', '5-10', '10+', etc."
    )
    bio_introduction = models.TextField(
        max_length=500, 
        blank=True,
        help_text="Add a few interesting things about yourself"
    )
    location = models.CharField(max_length=100, blank=True, help_text="Specify your current location")
    
    # Verification & Onboarding
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    onboarding_step = models.CharField(max_length=20, choices=ONBOARDING_STATUS_CHOICES, default='PROFILE_SETUP')
    onboarding_completed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_profiles'

    def __str__(self):
        return f"{self.user.full_name} - Professional"

    def update_onboarding_step(self, step):
        """Update onboarding step and mark as completed if final step"""
        self.onboarding_step = step
        if step == 'COMPLETED':
            self.onboarding_completed = True
        self.save()


# Step 2: Document Upload Model - 
class ProfessionalDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('GOVERNMENT_ID', 'Government ID'),
        ('PASSPORT', 'Passport'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('PROFESSIONAL_LICENSE', 'Professional License/Bar Certificate'),
        ('DEGREE_CERTIFICATE', 'Law Degree Certificate'),
        ('OTHER', 'Other'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    
    # Document stored as binary data
    document_data = models.BinaryField(blank=True, null=True)
    document_name = models.CharField(max_length=255, blank=True, null=True)
    document_content_type = models.CharField(max_length=100, blank=True, null=True)
    document_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    
    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'professional_documents'
        unique_together = ['professional', 'document_type']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.get_document_type_display()}"


# Step 3: Video KYC Model 
class VideoKYC(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('COMPLETED', 'Completed'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='video_kyc_sessions')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NOT_STARTED')
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Video file storage fields
    video_data = models.BinaryField(null=True, blank=True)
    video_name = models.CharField(max_length=255, null=True, blank=True)
    video_content_type = models.CharField(max_length=100, null=True, blank=True)
    video_size = models.IntegerField(null=True, blank=True)
    session_data = models.TextField(null=True, blank=True)  # Store session metadata as JSON

    class Meta:
        db_table = 'video_kyc_sessions'

    def __str__(self):
        return f"KYC - {self.professional.user.full_name} - {self.status}"


# Step 4: Portfolio Model - 
class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='portfolios')
    
    # Basic Information - only name and document
    name = models.CharField(max_length=200)
    
    # Document stored as binary data
    document_data = models.BinaryField(blank=True, null=True)
    document_name = models.CharField(max_length=255, blank=True, null=True)
    document_content_type = models.CharField(max_length=100, blank=True, null=True)
    document_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'professional_portfolios'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.name}"



# Step 5: Consultation Hours Model - 
class ConsultationAvailability(models.Model):
    CONSULTATION_TYPE_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('BOTH', 'Both'),
    ]

    DURATION_CHOICES = [
        (30, '30 minutes'),
        (60, '1 hour'),
        (90, '1.5 hours'),
        (120, '2 hours'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='availability')
    
    # Available Days - Monday to Sunday
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    # Time Range
    from_time = models.TimeField()  # Start time
    to_time = models.TimeField()    # End time
    
    # Consultation Types
    consultation_type = models.CharField(max_length=10, choices=CONSULTATION_TYPE_CHOICES, default='BOTH')
    
    # Duration Settings
    consultation_duration_minutes = models.IntegerField(choices=DURATION_CHOICES, default=60)
    
    # Calendar Integration (checkboxes for frontend)
    google_calendar_sync = models.BooleanField(default=False)
    outlook_calendar_sync = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_availability'

    def __str__(self):
        return f"{self.professional.user.full_name} - Availability"

    def get_available_days(self):
        """Return list of available days"""
        days = []
        if self.monday: days.append('Monday')
        if self.tuesday: days.append('Tuesday')
        if self.wednesday: days.append('Wednesday')
        if self.thursday: days.append('Thursday')
        if self.friday: days.append('Friday')
        if self.saturday: days.append('Saturday')
        if self.sunday: days.append('Sunday')
        return days


# Step 6: Payment Method Models - 
class PaymentMethod(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('BANK_ACCOUNT', 'Bank Account'),
        ('DIGITAL_WALLET', 'Digital Wallet'),
    ]
    
    DIGITAL_WALLET_CHOICES = [
        ('PAYTM', 'Paytm'),
        ('GOOGLE_PAY', 'Google Pay'),
        ('PHONEPE', 'PhonePe'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES)
    
    # Bank Account Details (if bank account is selected)
    account_holder_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=15, blank=True)
    
    # Digital Wallet Details (if digital wallet is selected)
    wallet_provider = models.CharField(max_length=15, choices=DIGITAL_WALLET_CHOICES, blank=True)
    wallet_phone_number = models.CharField(max_length=15, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_payment_methods'

    def __str__(self):
        if self.payment_type == 'BANK_ACCOUNT':
            return f"{self.professional.user.full_name} - {self.bank_name} Account"
        else:
            return f"{self.professional.user.full_name} - {self.get_wallet_provider_display()}"





class ProfessionalPricing(models.Model):
    """Pricing structure for professionals"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.OneToOneField(ProfessionalProfile, on_delete=models.CASCADE, related_name='pricing')
    
    # Consultation fees by duration
    fee_30_min = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    fee_60_min = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    fee_90_min = models.DecimalField(max_digits=10, decimal_places=2, default=1400.00)
    fee_120_min = models.DecimalField(max_digits=10, decimal_places=2, default=1800.00)
    
    # Additional charges
    offline_consultation_extra = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    
    # Settings
    accepts_online = models.BooleanField(default=True)
    accepts_offline = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_pricing'

    def __str__(self):
        return f"Pricing for {self.professional.user.full_name}"
    
    def get_fee_for_duration(self, duration_minutes):
        """Get consultation fee based on duration"""
        fee_mapping = {
            30: self.fee_30_min,
            60: self.fee_60_min,
            90: self.fee_90_min,
            120: self.fee_120_min,
        }
        return fee_mapping.get(duration_minutes, self.fee_60_min)


class ConsultationSlot(models.Model):
    """Time slots for consultations"""
    
    SLOT_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BOOKED', 'Booked'),
        ('BLOCKED', 'Blocked'),
        ('HELD', 'Temporarily Held'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='consultation_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=SLOT_STATUS_CHOICES, default='AVAILABLE')
    
    # If slot is booked
    # booking = models.ForeignKey(ConsultationBooking, on_delete=models.CASCADE, null=True, blank=True, related_name='slots')
    
    # If slot is temporarily held
    held_until = models.DateTimeField(null=True, blank=True)
    held_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_slots')
    
    # Custom rate for this specific slot (optional override)
    custom_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_slots'
        unique_together = ['professional', 'start_time', 'end_time']
        ordering = ['start_time']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.start_time} to {self.end_time} ({self.status})"

    def is_available(self):
        """Check if slot is available for booking"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.status != 'AVAILABLE':
            return False
        
        if self.start_time <= now:
            return False
            
        # If held, check if hold has expired
        if self.status == 'HELD' and self.held_until and now > self.held_until:
            self.status = 'AVAILABLE'
            self.held_by = None
            self.held_until = None
            self.save()
            
        return self.status == 'AVAILABLE'

    def hold_slot(self, user, duration_minutes=15):
        """Temporarily hold slot for a user"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.is_available():
            return False
            
        self.status = 'HELD'
        self.held_by = user
        self.held_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save()
        return True

    def release_hold(self):
        """Release temporary hold on slot"""
        if self.status == 'HELD':
            self.status = 'AVAILABLE'
            self.held_by = None
            self.held_until = None
            self.save()


class ConsultationBooking(models.Model):
    """Booking system for consultations"""
    
    BOOKING_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED_BY_CLIENT', 'Cancelled by Client'),
        ('CANCELLED_BY_PROFESSIONAL', 'Cancelled by Professional'),
        ('NO_SHOW', 'No Show'),
    ]
    
    CONSULTATION_TYPE_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='bookings')
    consultation_slot = models.ForeignKey(ConsultationSlot, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking Details
    consultation_type = models.CharField(max_length=10, choices=CONSULTATION_TYPE_CHOICES)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=30, choices=BOOKING_STATUS_CHOICES, default='PENDING')
    
    # Client Information
    client_problem_description = models.TextField(max_length=1000, blank=True)
    client_contact_preference = models.CharField(max_length=50, blank=True)
    
    # Meeting Details (for online consultations)
    meeting_link = models.URLField(blank=True, null=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    meeting_password = models.CharField(max_length=50, blank=True, null=True)
    
    # Location Details (for offline consultations)
    consultation_address = models.TextField(max_length=500, blank=True)
    
    # Booking Timestamps
    booked_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation Details
    cancellation_reason = models.TextField(max_length=500, blank=True)
    cancelled_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings')
    
    # Payment Details
    payment_status = models.CharField(max_length=20, default='PENDING')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking: {self.client.full_name} -> {self.professional.user.full_name} ({self.booking_status})"
    
    def can_be_cancelled_by_client(self):
        """Check if booking can be cancelled by client"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.booking_status not in ['PENDING', 'CONFIRMED']:
            return False
        
        # Allow cancellation up to 2 hours before the consultation
        cancellation_deadline = self.consultation_slot.start_time - timedelta(hours=2)
        return timezone.now() < cancellation_deadline
    
    def can_be_cancelled_by_professional(self):
        """Check if booking can be cancelled by professional"""
        return self.booking_status in ['PENDING', 'CONFIRMED']
    
    def cancel_booking(self, cancelled_by_user, reason=""):
        """Cancel the booking"""
        from django.utils import timezone
        
        if cancelled_by_user == self.client:
            if not self.can_be_cancelled_by_client():
                return False, "Booking cannot be cancelled at this time"
            self.booking_status = 'CANCELLED_BY_CLIENT'
        elif cancelled_by_user == self.professional.user:
            if not self.can_be_cancelled_by_professional():
                return False, "Booking cannot be cancelled at this time"
            self.booking_status = 'CANCELLED_BY_PROFESSIONAL'
        else:
            return False, "User not authorized to cancel this booking"
        
        self.cancelled_by = cancelled_by_user
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        
        # Free up the consultation slot
        self.consultation_slot.status = 'AVAILABLE'
        self.consultation_slot.save()
        
        self.save()
        return True, "Booking cancelled successfully"


class ProfessionalReview(models.Model):
    """Simple review system for professionals"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_given')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Simple Review - just rating and note
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    review_note = models.TextField(max_length=500, blank=True, help_text="Optional review note")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_reviews'
        ordering = ['-created_at']
        unique_together = ['client', 'professional']  # One review per client per professional

    def __str__(self):
        return f"Review: {self.client.full_name} -> {self.professional.user.full_name} ({self.rating}/5)"


class ProfessionalReviewSummary(models.Model):
    """Simple aggregated review statistics for professionals"""
    
    professional = models.OneToOneField(ProfessionalProfile, on_delete=models.CASCADE, related_name='review_summary')
    
    # Basic Statistics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    
    # Rating Distribution
    five_star_count = models.IntegerField(default=0)
    four_star_count = models.IntegerField(default=0)
    three_star_count = models.IntegerField(default=0)
    two_star_count = models.IntegerField(default=0)
    one_star_count = models.IntegerField(default=0)
    
    # Last Updated
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_review_summaries'

    def __str__(self):
        return f"Review Summary: {self.professional.user.full_name} ({self.average_rating}/5.0)"
    
    def update_summary(self):
        """Update review summary statistics"""
        from django.db.models import Avg, Count
        
        reviews = ProfessionalReview.objects.filter(professional=self.professional)
        
        # Basic statistics
        self.total_reviews = reviews.count()
        
        if self.total_reviews > 0:
            # Average rating
            avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
            self.average_rating = round(avg_rating or 0, 2)
            
            # Rating distribution
            rating_counts = reviews.values('rating').annotate(count=Count('rating'))
            rating_dict = {item['rating']: item['count'] for item in rating_counts}
            
            self.five_star_count = rating_dict.get(5, 0)
            self.four_star_count = rating_dict.get(4, 0)
            self.three_star_count = rating_dict.get(3, 0)
            self.two_star_count = rating_dict.get(2, 0)
            self.one_star_count = rating_dict.get(1, 0)
        else:
            # Reset to defaults if no reviews
            self.average_rating = 0.00
            self.five_star_count = 0
            self.four_star_count = 0
            self.three_star_count = 0
            self.two_star_count = 0
            self.one_star_count = 0
        
        self.save()



