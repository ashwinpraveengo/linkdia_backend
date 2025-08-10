import graphene
from graphene_django import DjangoObjectType
# from core.models import NotificationTemplate, Notification  # Commented out until implemented


# Enum Types based on model choices
class UserTypeEnum(graphene.Enum):
    PROFESSIONAL = 'PROFESSIONAL'
    CLIENT = 'CLIENT'


class VerificationStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    IN_REVIEW = 'IN_REVIEW'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'


class OnboardingStatusEnum(graphene.Enum):
    PROFILE_SETUP = 'PROFILE_SETUP'
    DOCUMENT_UPLOAD = 'DOCUMENT_UPLOAD'
    VIDEO_KYC = 'VIDEO_KYC'
    PORTFOLIO = 'PORTFOLIO'
    CONSULTATION_HOURS = 'CONSULTATION_HOURS'
    PAYMENT_SETUP = 'PAYMENT_SETUP'
    COMPLETED = 'COMPLETED'


class ExpertiseAreaEnum(graphene.Enum):
    CRIMINAL_LAWYER = 'CRIMINAL_LAWYER'
    CORPORATE_LAWYER = 'CORPORATE_LAWYER'
    FAMILY_LAWYER = 'FAMILY_LAWYER'
    REAL_ESTATE_LAWYER = 'REAL_ESTATE_LAWYER'
    IMMIGRATION_LAWYER = 'IMMIGRATION_LAWYER'
    PERSONAL_INJURY_LAWYER = 'PERSONAL_INJURY_LAWYER'
    INTELLECTUAL_PROPERTY_LAWYER = 'INTELLECTUAL_PROPERTY_LAWYER'
    TAX_LAWYER = 'TAX_LAWYER'
    EMPLOYMENT_LAWYER = 'EMPLOYMENT_LAWYER'
    ENVIRONMENTAL_LAWYER = 'ENVIRONMENTAL_LAWYER'
    OTHER = 'OTHER'


class DocumentTypeEnum(graphene.Enum):
    GOVERNMENT_ID = 'GOVERNMENT_ID'
    PASSPORT = 'PASSPORT'
    DRIVING_LICENSE = 'DRIVING_LICENSE'
    PROFESSIONAL_LICENSE = 'PROFESSIONAL_LICENSE'
    DEGREE_CERTIFICATE = 'DEGREE_CERTIFICATE'
    EXPERIENCE_CERTIFICATE = 'EXPERIENCE_CERTIFICATE'
    PRACTICE_CERTIFICATE = 'PRACTICE_CERTIFICATE'
    REGISTRATION_CERTIFICATE = 'REGISTRATION_CERTIFICATE'
    OTHER = 'OTHER'


class VideoKYCStatusEnum(graphene.Enum):
    NOT_STARTED = 'NOT_STARTED'
    READY_TO_START = 'READY_TO_START'
    SCHEDULED = 'SCHEDULED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    RESCHEDULED = 'RESCHEDULED'


class PortfolioStatusEnum(graphene.Enum):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    ARCHIVED = 'ARCHIVED'


class OrganizationTypeEnum(graphene.Enum):
    LAW_FIRM = 'LAW_FIRM'
    SOLO_PRACTICE = 'SOLO_PRACTICE'
    CORPORATE_LEGAL = 'CORPORATE_LEGAL'
    NGO = 'NGO'
    GOVERNMENT = 'GOVERNMENT'
    OTHER = 'OTHER'


class ConsultationTypeEnum(graphene.Enum):
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    BOTH = 'BOTH'


class DurationEnum(graphene.Enum):
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    ONE_HOUR_THIRTY = 90
    TWO_HOURS = 120
    THREE_HOURS = 180


class PaymentTypeEnum(graphene.Enum):
    BANK_ACCOUNT = 'BANK_ACCOUNT'
    DIGITAL_WALLET = 'DIGITAL_WALLET'


class DigitalWalletEnum(graphene.Enum):
    PAYTM = 'PAYTM'
    GOOGLE_PAY = 'GOOGLE_PAY'
    PHONEPE = 'PHONEPE'
    PAYPAL = 'PAYPAL'
    RAZORPAY = 'RAZORPAY'
    STRIPE = 'STRIPE'


class PaymentStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    VERIFIED = 'VERIFIED'
    REJECTED = 'REJECTED'
    SUSPENDED = 'SUSPENDED'


class BookingStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED_BY_CLIENT = 'CANCELLED_BY_CLIENT'
    CANCELLED_BY_PROFESSIONAL = 'CANCELLED_BY_PROFESSIONAL'
    COMPLETED = 'COMPLETED'
    NO_SHOW = 'NO_SHOW'
    RESCHEDULED = 'RESCHEDULED'


class BookingPaymentStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'
    PARTIAL_REFUND = 'PARTIAL_REFUND'


class UrgencyLevelEnum(graphene.Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    URGENT = 'URGENT'


class RatingEnum(graphene.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class BookingActionEnum(graphene.Enum):
    CREATED = 'CREATED'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    RESCHEDULED = 'RESCHEDULED'
    COMPLETED = 'COMPLETED'
    PAYMENT_MADE = 'PAYMENT_MADE'
    PAYMENT_FAILED = 'PAYMENT_FAILED'
    REFUND_PROCESSED = 'REFUND_PROCESSED'
    REMINDER_SENT = 'REMINDER_SENT'
    NOTE_ADDED = 'NOTE_ADDED'


class SlotStatusEnum(graphene.Enum):
    AVAILABLE = 'AVAILABLE'
    BOOKED = 'BOOKED'
    BLOCKED = 'BLOCKED'
    TEMPORARY_HOLD = 'TEMPORARY_HOLD'


class NotificationChannelEnum(graphene.Enum):
    EMAIL = 'EMAIL'
    SMS = 'SMS'
    PUSH = 'PUSH'
    IN_APP = 'IN_APP'


class NotificationStatusEnum(graphene.Enum):
    PENDING = 'PENDING'
    SENT = 'SENT'
    DELIVERED = 'DELIVERED'
    READ = 'READ'
    FAILED = 'FAILED'




# Common Response Types
class SuccessResponseType(graphene.ObjectType):
    """Generic success response type"""
    success = graphene.Boolean()
    message = graphene.String()


class AuthPayloadType(graphene.ObjectType):
    """Authentication response type"""
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field('core.types.user.UserType')
    access_token = graphene.String()
    refresh_token = graphene.String()



class SlotPayloadType(graphene.ObjectType):
    """Slot operation response type"""
    success = graphene.Boolean()
    message = graphene.String()
    slot = graphene.Field('core.types.booking.ConsultationSlotType')
    errors = graphene.List(graphene.String)


class ValidationErrorType(graphene.ObjectType):
    """Validation error response type"""
    field = graphene.String()
    message = graphene.String()


class ErrorResponseType(graphene.ObjectType):
    """Generic error response type"""
    success = graphene.Boolean(default_value=False)
    message = graphene.String()
    errors = graphene.List(ValidationErrorType)
    code = graphene.String()


# Pagination Types
class PageInfoType(graphene.ObjectType):
    """Page information for pagination"""
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    start_cursor = graphene.String()
    end_cursor = graphene.String()
    total_count = graphene.Int()


class PaginatedResult(graphene.ObjectType):
    """Base class for paginated results"""
    total = graphene.Int()
    page = graphene.Int()
    page_size = graphene.Int()
    total_pages = graphene.Int()


class PaginationInputType(graphene.InputObjectType):
    """Input type for pagination"""
    first = graphene.Int()
    after = graphene.String()
    last = graphene.Int()
    before = graphene.String()


# Search and Filter Types
class SearchInputType(graphene.InputObjectType):
    """Input type for search functionality"""
    query = graphene.String()
    location = graphene.String()
    expertise_area = graphene.String()
    min_rating = graphene.Float()
    max_rate = graphene.Decimal()
    availability_date = graphene.Date()
    consultation_type = graphene.String()


class SortInputType(graphene.InputObjectType):
    """Input type for sorting"""
    field = graphene.String()
    order = graphene.String()  # ASC or DESC


# Analytics Types
class ProfessionalStatsType(graphene.ObjectType):
    """Professional statistics type"""
    total_consultations = graphene.Int()
    total_earnings = graphene.Decimal()
    average_rating = graphene.Float()
    total_reviews = graphene.Int()
    completion_rate = graphene.Float()
    response_time = graphene.String()
    this_month_bookings = graphene.Int()
    this_month_earnings = graphene.Decimal()


class ClientStatsType(graphene.ObjectType):
    """Client statistics type"""
    total_bookings = graphene.Int()
    total_spent = graphene.Decimal()
    favorite_professionals = graphene.List(graphene.ID)
    consultation_history_count = graphene.Int()


# File Upload Types
class FileUploadType(graphene.ObjectType):
    """File upload response type"""
    success = graphene.Boolean()
    file_url = graphene.String()
    file_name = graphene.String()
    file_size = graphene.Int()
    message = graphene.String()


class FileInputType(graphene.InputObjectType):
    """File input type"""
    file = graphene.String()  # Base64 encoded file or file path
    filename = graphene.String()
    content_type = graphene.String()
