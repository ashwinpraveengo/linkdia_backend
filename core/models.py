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
    profile_picture = models.URLField(blank=True, null=True)
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
        ('PORTFOLIO', 'Portfolio & Case Studies'),
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
    
    # Profile Setup Fields (from Image 1)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    area_of_expertise = models.CharField(max_length=50, choices=EXPERTISE_AREA_CHOICES, blank=True)
    years_of_experience = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    bio_introduction = models.TextField(
        max_length=500, 
        blank=True,
        help_text="Add a few interesting things about yourself"
    )
    location = models.CharField(max_length=100, blank=True, help_text="Specify your current location")
    
    # Additional Professional Details
    specialization = models.CharField(max_length=200, blank=True)
    education = models.TextField(blank=True)
    languages = models.CharField(max_length=300, blank=True)  # Comma-separated
    professional_license_number = models.CharField(max_length=100, blank=True)
    bar_registration_number = models.CharField(max_length=100, blank=True)
    
    # Location & Availability
    timezone = models.CharField(max_length=50, blank=True)
    is_available = models.BooleanField(default=True)
    
    # Verification & Onboarding
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    onboarding_step = models.CharField(max_length=20, choices=ONBOARDING_STATUS_CHOICES, default='PROFILE_SETUP')
    onboarding_completed = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    
    # Ratings & Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    total_consultations = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

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

    @property
    def completion_percentage(self):
        """Calculate profile completion percentage"""
        fields_to_check = [
            bool(self.profile_picture),
            bool(self.area_of_expertise),
            bool(self.years_of_experience),
            bool(self.bio_introduction),
            bool(self.location),
        ]
        completed_fields = sum(fields_to_check)
        return (completed_fields / len(fields_to_check)) * 100

    def update_rating(self):
        """Update average rating based on reviews"""
        from django.db.models import Avg
        reviews = self.reviews_received.filter(is_published=True)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        self.average_rating = avg_rating if avg_rating else 0.00
        self.total_reviews = reviews.count()
        self.save()


# Document Upload Model (from Image 2)
class ProfessionalDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('GOVERNMENT_ID', 'Government ID'),
        ('PASSPORT', 'Passport'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('PROFESSIONAL_LICENSE', 'Professional License/Bar Certificate'),
        ('DEGREE_CERTIFICATE', 'Law Degree Certificate'),
        ('EXPERIENCE_CERTIFICATE', 'Experience Certificate'),
        ('PRACTICE_CERTIFICATE', 'Practice Certificate'),
        ('REGISTRATION_CERTIFICATE', 'Bar Registration Certificate'),
        ('OTHER', 'Other'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(
        upload_to='professional_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])]
    )
    document_number = models.CharField(max_length=100, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    
    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    verification_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    
    # Additional metadata
    file_size = models.BigIntegerField(null=True, blank=True)  # in bytes
    original_filename = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'professional_documents'
        unique_together = ['professional', 'document_type']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.get_document_type_display()}"

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    def clean(self):
        # Ensure minimum 2 documents are uploaded
        if self.pk is None:  # New document
            doc_count = ProfessionalDocument.objects.filter(professional=self.professional).count()
            if doc_count == 0:
                # First document should be Government ID or similar
                required_types = ['GOVERNMENT_ID', 'PASSPORT', 'DRIVING_LICENSE']
                if self.document_type not in required_types:
                    raise ValidationError("First document must be a valid government-issued ID")


# Video KYC Model (from Image 3)
class VideoKYC(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('READY_TO_START', 'Ready to Start'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='video_kyc_sessions')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NOT_STARTED')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    
    # Instructions acknowledgment (from Image 3)
    camera_instruction_acknowledged = models.BooleanField(default=False)
    id_ready_acknowledged = models.BooleanField(default=False)
    
    # Video session details
    session_id = models.CharField(max_length=100, blank=True)  # Third-party video service session ID
    meeting_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Verification details
    verified_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_verifications')
    verification_notes = models.TextField(blank=True)
    identity_confirmed = models.BooleanField(default=False)
    face_match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    document_verification_passed = models.BooleanField(default=False)
    
    # Rescheduling
    reschedule_reason = models.TextField(blank=True)
    reschedule_count = models.IntegerField(default=0)
    max_reschedules = models.IntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'video_kyc_sessions'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"KYC - {self.professional.user.full_name} - {self.status}"

    def can_reschedule(self):
        return self.reschedule_count < self.max_reschedules

    def mark_ready_to_start(self):
        """Mark KYC as ready when both instructions are acknowledged"""
        if self.camera_instruction_acknowledged and self.id_ready_acknowledged:
            self.status = 'READY_TO_START'
            self.save()


# Portfolio & Case Studies Model (from Image 4)
class Portfolio(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='portfolios')
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    case_overview = models.TextField(blank=True)
    
    # Professional Organization/Firm Details (from Image 4 text)
    organization_name = models.CharField(max_length=200, blank=True)
    organization_type = models.CharField(
        max_length=50,
        choices=[
            ('LAW_FIRM', 'Law Firm'),
            ('SOLO_PRACTICE', 'Solo Practice'),
            ('CORPORATE_LEGAL', 'Corporate Legal Department'),
            ('NGO', 'Non-Profit Organization'),
            ('GOVERNMENT', 'Government Agency'),
            ('OTHER', 'Other'),
        ],
        blank=True
    )
    
    # Case Details
    practice_area = models.CharField(max_length=100, blank=True)
    case_type = models.CharField(max_length=100, blank=True)
    client_industry = models.CharField(max_length=100, blank=True)
    case_duration = models.CharField(max_length=100, blank=True)
    case_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    outcome = models.TextField(blank=True)
    
    # Professional Recognition
    awards_recognition = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    notable_mentions = models.TextField(blank=True)
    
    # Media and Documentation
    featured_image = models.ImageField(upload_to='portfolio_images/', null=True, blank=True)
    portfolio_document = models.FileField(
        upload_to='portfolio_documents/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    # Settings
    is_featured = models.BooleanField(default=False)
    is_confidential = models.BooleanField(default=False)  # Hide sensitive client info
    display_order = models.IntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_portfolios'
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.title}"


class PortfolioImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio_images/')
    caption = models.CharField(max_length=200, blank=True)
    display_order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portfolio_images'
        ordering = ['display_order']

    def __str__(self):
        return f"{self.portfolio.title} - Image {self.display_order}"


# Consultation Hours Model (from Image 5)
class ConsultationAvailability(models.Model):
    DAY_CHOICES = [
        ('M', 'Monday'),
        ('T', 'Tuesday'),
        ('W', 'Wednesday'),
        ('T', 'Thursday'),
        ('F', 'Friday'),
        ('S', 'Saturday'),
        ('S', 'Sunday'),
    ]

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
        (180, '3 hours'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='availability')
    
    # Available Days (from Image 5)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    # Time Range (from Image 5)
    start_time = models.TimeField()  # Default: 09:00 AM
    end_time = models.TimeField()    # Default: 09:00 PM
    
    # Consultation Types (from Image 5)
    consultation_type = models.CharField(max_length=10, choices=CONSULTATION_TYPE_CHOICES, default='BOTH')
    
    # Duration Settings (from Image 5)
    default_duration_minutes = models.IntegerField(choices=DURATION_CHOICES, default=60)
    
    # Calendar Integration (from Image 5)
    outlook_calendar_sync = models.BooleanField(default=False)
    google_calendar_sync = models.BooleanField(default=False)
    outlook_calendar_id = models.CharField(max_length=255, blank=True)
    google_calendar_id = models.CharField(max_length=255, blank=True)
    
    # Additional Settings
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    buffer_time_minutes = models.IntegerField(default=15)  # Break between sessions
    max_sessions_per_day = models.IntegerField(null=True, blank=True)
    advance_booking_days = models.IntegerField(default=30)  # How far in advance clients can book
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_availability'
        ordering = ['created_at']

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

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time')


# Payment Method Models (from Image 6)
class PaymentMethod(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('BANK_ACCOUNT', 'Bank Account'),
        ('DIGITAL_WALLET', 'Digital Wallet'),
    ]
    
    DIGITAL_WALLET_CHOICES = [
        ('PAYTM', 'Paytm'),
        ('GOOGLE_PAY', 'Google Pay'),
        ('PHONEPE', 'PhonePe'),
        ('PAYPAL', 'PayPal'),
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES)
    
    # Bank Account Details (from Image 6 - middle screen)
    account_holder_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=15, blank=True)  # For Indian banks
    routing_number = models.CharField(max_length=20, blank=True)  # For international
    swift_code = models.CharField(max_length=15, blank=True)
    
    # Digital Wallet Details (from Image 6 - right screen)
    wallet_provider = models.CharField(max_length=15, choices=DIGITAL_WALLET_CHOICES, blank=True)
    wallet_phone_number = models.CharField(max_length=15, blank=True)
    wallet_email = models.EmailField(blank=True)
    wallet_account_id = models.CharField(max_length=100, blank=True)
    
    # Verification
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    minimum_payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_payment_methods'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        if self.payment_type == 'BANK_ACCOUNT':
            return f"{self.professional.user.full_name} - {self.bank_name} Account"
        else:
            return f"{self.professional.user.full_name} - {self.get_wallet_provider_display()}"

    def save(self, *args, **kwargs):
        # Ensure only one default payment method per professional
        if self.is_default:
            PaymentMethod.objects.filter(
                professional=self.professional, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.payment_type == 'BANK_ACCOUNT':
            required_fields = ['account_holder_name', 'bank_name', 'account_number']
            if not all(getattr(self, field) for field in required_fields):
                raise ValidationError("Bank account details are incomplete")
                
        elif self.payment_type == 'DIGITAL_WALLET':
            if not self.wallet_provider:
                raise ValidationError("Digital wallet provider must be selected")
            if not (self.wallet_phone_number or self.wallet_email):
                raise ValidationError("Either phone number or email is required for digital wallet")


# Enhanced Onboarding Progress Tracking
class OnboardingProgress(models.Model):
    professional = models.OneToOneField(ProfessionalProfile, on_delete=models.CASCADE, related_name='onboarding_progress')
    
    # Step 1: Profile Setup
    profile_setup_completed = models.BooleanField(default=False)
    profile_setup_completed_at = models.DateTimeField(null=True, blank=True)
    profile_completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Step 2: Document Upload  
    documents_uploaded = models.BooleanField(default=False)
    documents_uploaded_at = models.DateTimeField(null=True, blank=True)
    documents_verified = models.BooleanField(default=False)
    documents_verified_at = models.DateTimeField(null=True, blank=True)
    total_documents_uploaded = models.IntegerField(default=0)
    minimum_documents_required = models.IntegerField(default=2)
    
    # Step 3: Video KYC
    video_kyc_scheduled = models.BooleanField(default=False)
    video_kyc_scheduled_at = models.DateTimeField(null=True, blank=True)
    video_kyc_completed = models.BooleanField(default=False)
    video_kyc_completed_at = models.DateTimeField(null=True, blank=True)
    video_kyc_verified = models.BooleanField(default=False)
    video_kyc_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Step 4: Portfolio & Case Studies
    portfolio_added = models.BooleanField(default=False)
    portfolio_added_at = models.DateTimeField(null=True, blank=True)
    portfolio_documents_uploaded = models.BooleanField(default=False)
    portfolio_documents_uploaded_at = models.DateTimeField(null=True, blank=True)
    
    # Step 5: Consultation Hours
    availability_set = models.BooleanField(default=False)
    availability_set_at = models.DateTimeField(null=True, blank=True)
    calendar_synced = models.BooleanField(default=False)
    calendar_synced_at = models.DateTimeField(null=True, blank=True)
    
    # Step 6: Payment Setup
    payment_method_added = models.BooleanField(default=False)
    payment_method_added_at = models.DateTimeField(null=True, blank=True)
    payment_verified = models.BooleanField(default=False)
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Overall completion
    onboarding_completed = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'onboarding_progress'

    def __str__(self):
        return f"{self.professional.user.full_name} - Onboarding Progress"

    def calculate_completion_percentage(self):
        """Calculate overall completion percentage based on all steps"""
        steps = [
            self.profile_setup_completed,
            self.documents_uploaded and self.documents_verified,
            self.video_kyc_completed and self.video_kyc_verified,
            self.portfolio_added,
            self.availability_set,
            self.payment_method_added and self.payment_verified,
        ]
        completed_steps = sum(steps)
        return round((completed_steps / len(steps)) * 100, 2)

    def get_current_step(self):
        """Get the current step in the onboarding process"""
        if not self.profile_setup_completed:
            return 'PROFILE_SETUP'
        elif not (self.documents_uploaded and self.documents_verified):
            return 'DOCUMENT_UPLOAD'
        elif not (self.video_kyc_completed and self.video_kyc_verified):
            return 'VIDEO_KYC'
        elif not self.portfolio_added:
            return 'PORTFOLIO'
        elif not self.availability_set:
            return 'CONSULTATION_HOURS'
        elif not (self.payment_method_added and self.payment_verified):
            return 'PAYMENT_SETUP'
        else:
            return 'COMPLETED'

    def get_next_step_instructions(self):
        """Get instructions for the next step"""
        current_step = self.get_current_step()
        
        instructions = {
            'PROFILE_SETUP': "Complete your profile setup with photo, expertise area, and bio",
            'DOCUMENT_UPLOAD': f"Upload at least {self.minimum_documents_required} documents for verification",
            'VIDEO_KYC': "Schedule and complete video KYC to validate your authenticity", 
            'PORTFOLIO': "Add portfolio items and case studies to showcase your work",
            'CONSULTATION_HOURS': "Set your availability and consultation preferences",
            'PAYMENT_SETUP': "Add and verify your payment method to receive payments",
            'COMPLETED': "Your onboarding is complete! You can now start receiving consultations"
        }
        
        return instructions.get(current_step, "")

    def mark_step_completed(self, step):
        """Mark a specific step as completed with timestamp"""
        now = timezone.now()
        
        step_mappings = {
            'PROFILE_SETUP': ('profile_setup_completed', 'profile_setup_completed_at'),
            'DOCUMENTS_UPLOADED': ('documents_uploaded', 'documents_uploaded_at'),
            'DOCUMENTS_VERIFIED': ('documents_verified', 'documents_verified_at'),
            'VIDEO_KYC_SCHEDULED': ('video_kyc_scheduled', 'video_kyc_scheduled_at'),
            'VIDEO_KYC_COMPLETED': ('video_kyc_completed', 'video_kyc_completed_at'),
            'VIDEO_KYC_VERIFIED': ('video_kyc_verified', 'video_kyc_verified_at'),
            'PORTFOLIO_ADDED': ('portfolio_added', 'portfolio_added_at'),
            'PORTFOLIO_DOCUMENTS_UPLOADED': ('portfolio_documents_uploaded', 'portfolio_documents_uploaded_at'),
            'AVAILABILITY_SET': ('availability_set', 'availability_set_at'),
            'CALENDAR_SYNCED': ('calendar_synced', 'calendar_synced_at'),
            'PAYMENT_METHOD_ADDED': ('payment_method_added', 'payment_method_added_at'),
            'PAYMENT_VERIFIED': ('payment_verified', 'payment_verified_at'),
        }
        
        if step in step_mappings:
            field_name, timestamp_field = step_mappings[step]
            setattr(self, field_name, True)
            setattr(self, timestamp_field, now)
        
        # Check if all steps are completed
        completion_percentage = self.calculate_completion_percentage()
        if completion_percentage == 100:
            self.onboarding_completed = True
            self.onboarding_completed_at = now
            # Update the professional profile
            self.professional.onboarding_completed = True
            self.professional.onboarding_step = 'COMPLETED'
            self.professional.save()
        
        self.save()


# Additional Settings Model
class ProfessionalSettings(models.Model):
    professional = models.OneToOneField(ProfessionalProfile, on_delete=models.CASCADE, related_name='settings')
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Booking Settings
    auto_accept_bookings = models.BooleanField(default=False)
    require_advance_payment = models.BooleanField(default=True)
    cancellation_hours = models.IntegerField(default=24)  # Hours before booking
    
    # Privacy Settings
    show_phone_number = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    public_profile = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professional_settings'

    def __str__(self):
        return f"{self.professional.user.full_name} - Settings"


# Booking System Models
class ConsultationBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED_BY_CLIENT', 'Cancelled by Client'),
        ('CANCELLED_BY_PROFESSIONAL', 'Cancelled by Professional'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    
    CONSULTATION_TYPE_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIAL_REFUND', 'Partial Refund'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings_as_client')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking Details
    consultation_date = models.DateTimeField()
    duration_minutes = models.IntegerField()
    consultation_type = models.CharField(max_length=10, choices=CONSULTATION_TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    
    # Meeting Details
    meeting_link = models.URLField(blank=True)  # For online consultations
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Location Details (for offline consultations)
    location_address = models.TextField(blank=True)
    location_notes = models.TextField(blank=True)
    
    # Client Details
    client_notes = models.TextField(blank=True, help_text="Special requirements or notes from client")
    case_description = models.TextField(help_text="Brief description of the legal matter")
    urgency_level = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('URGENT', 'Urgent'),
        ],
        default='MEDIUM'
    )
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Confirmation and Communication
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='confirmed_bookings'
    )
    
    # Cancellation Details
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Completion Details
    completed_at = models.DateTimeField(null=True, blank=True)
    professional_notes = models.TextField(blank=True, help_text="Professional's notes after consultation")
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    # Reminders
    reminder_sent_24h = models.BooleanField(default=False)
    reminder_sent_1h = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_bookings'
        ordering = ['-consultation_date']

    def __str__(self):
        return f"Booking {str(self.id)[:8]} - {self.client.full_name} with {self.professional.user.full_name}"

    def save(self, *args, **kwargs):
        # Calculate final amount
        self.final_amount = self.total_amount - self.discount_amount + self.cancellation_fee
        super().save(*args, **kwargs)

    def can_cancel(self):
        """Check if booking can be cancelled based on professional's cancellation policy"""
        if self.status in ['CANCELLED_BY_CLIENT', 'CANCELLED_BY_PROFESSIONAL', 'COMPLETED']:
            return False
        
        cancellation_hours = getattr(self.professional.settings, 'cancellation_hours', 24)
        cancellation_deadline = self.consultation_date - timezone.timedelta(hours=cancellation_hours)
        return timezone.now() < cancellation_deadline

    def get_cancellation_fee(self):
        """Calculate cancellation fee based on timing"""
        if not self.can_cancel():
            return self.final_amount * 0.5  # 50% fee for late cancellation
        return 0.00

    @property
    def is_upcoming(self):
        return self.consultation_date > timezone.now() and self.status == 'CONFIRMED'

    @property
    def is_past(self):
        return self.consultation_date < timezone.now()


class BookingHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Booking Created'),
        ('CONFIRMED', 'Booking Confirmed'),
        ('CANCELLED', 'Booking Cancelled'),
        ('RESCHEDULED', 'Booking Rescheduled'),
        ('COMPLETED', 'Booking Completed'),
        ('PAYMENT_MADE', 'Payment Made'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('REFUND_PROCESSED', 'Refund Processed'),
        ('REMINDER_SENT', 'Reminder Sent'),
        ('NOTE_ADDED', 'Note Added'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(ConsultationBooking, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='performed_booking_actions'
    )
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_history'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.booking} - {self.action} at {self.timestamp}"


class ConsultationReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(ConsultationBooking, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_given')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Review Details
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField()
    
    # Specific Ratings
    communication_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    expertise_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    professionalism_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    value_for_money_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    # Review Status
    is_published = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='moderated_reviews'
    )
    
    # Recommendations
    would_recommend = models.BooleanField(default=True)
    tags = models.CharField(max_length=500, blank=True)  # Comma-separated tags
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.client.full_name} for {self.professional.user.full_name} - {self.rating} stars"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update professional's average rating
        self.professional.update_rating()


class ConsultationSlot(models.Model):
    """Available time slots for consultations"""
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BOOKED', 'Booked'),
        ('BLOCKED', 'Blocked'),
        ('TEMPORARY_HOLD', 'Temporary Hold'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE')
    
    # Linked booking if slot is booked
    booking = models.ForeignKey(
        ConsultationBooking, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='time_slot'
    )
    
    # For temporary holds (during booking process)
    held_until = models.DateTimeField(null=True, blank=True)
    held_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='held_slots'
    )
    
    # Pricing (can override default professional rate)
    custom_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consultation_slots'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.professional.user.full_name} - {self.start_time} to {self.end_time}"

    def is_available(self):
        """Check if slot is currently available for booking"""
        if self.status != 'AVAILABLE':
            return False
        
        # Check if temporary hold has expired
        if self.status == 'TEMPORARY_HOLD' and self.held_until:
            if timezone.now() > self.held_until:
                self.status = 'AVAILABLE'
                self.held_until = None
                self.held_by = None
                self.save()
                return True
            return False
        
        return True

    def hold_slot(self, user, minutes=15):
        """Temporarily hold a slot for booking process"""
        if self.is_available():
            self.status = 'TEMPORARY_HOLD'
            self.held_by = user
            self.held_until = timezone.now() + timezone.timedelta(minutes=minutes)
            self.save()
            return True
        return False

    def book_slot(self, booking):
        """Mark slot as booked"""
        self.status = 'BOOKED'
        self.booking = booking
        self.held_by = None
        self.held_until = None
        self.save()

    def release_slot(self):
        """Release a booked or held slot"""
        self.status = 'AVAILABLE'
        self.booking = None
        self.held_by = None
        self.held_until = None
        self.save()


class NotificationTemplate(models.Model):
    """Templates for various notification types"""
    TEMPLATE_TYPE_CHOICES = [
        ('BOOKING_CONFIRMATION', 'Booking Confirmation'),
        ('BOOKING_REMINDER', 'Booking Reminder'),
        ('BOOKING_CANCELLATION', 'Booking Cancellation'),
        ('BOOKING_RESCHEDULED', 'Booking Rescheduled'),
        ('PAYMENT_CONFIRMATION', 'Payment Confirmation'),
        ('REVIEW_REQUEST', 'Review Request'),
        ('WELCOME_CLIENT', 'Welcome Client'),
        ('WELCOME_PROFESSIONAL', 'Welcome Professional'),
    ]

    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    
    subject = models.CharField(max_length=200, blank=True)  # For emails
    content = models.TextField()
    
    # Template variables that can be used
    available_variables = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'
        unique_together = ['template_type', 'channel']

    def __str__(self):
        return f"{self.get_template_type_display()} - {self.get_channel_display()}"


class Notification(models.Model):
    """Individual notifications sent to users"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='sent_notifications')
    
    # Content (populated from template)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Delivery details
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    booking = models.ForeignKey(
        ConsultationBooking, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.email} - {self.template.template_type}"

    def mark_as_read(self):
        if self.status == 'DELIVERED':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save()