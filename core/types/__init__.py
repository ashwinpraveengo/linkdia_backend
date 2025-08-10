# Import all types for easy access
from .user import (
    UserType,
    ClientProfileType,
    PasswordResetTokenType,
    UserInputType,
    ClientProfileInputType,
    ProfessionalProfileInputType,
)

from .proffesional_profile import (
    ProfessionalProfileType,  # Use the complete one from proffesional_profile.py
    ProfessionalPricingType,
    ProfessionalReviewSummaryType,
    ProfessionalDocumentType,
    VideoKYCType,
    PortfolioType,
    ConsultationAvailabilityType,
    PaymentMethodType,
    OnboardingProgressType,
    ProfessionalSettingsType,
    ProfessionalDocumentInputType,
    VideoKYCInputType,
    PortfolioInputType,
    ConsultationAvailabilityInputType,
    PaymentMethodInputType,
    ProfessionalSettingsInputType,
)



from .analytics import (
    ProfessionalAnalyticsType,
    ClientAnalyticsType,
    PlatformAnalyticsType,
    RevenueAnalyticsType,
    UserEngagementAnalyticsType,
    PerformanceMetricsType,
    AnalyticsFilterInputType,
    RevenueFilterInputType,
    PerformanceFilterInputType,
    PeriodComparisonType,
    BenchmarkComparisonType,
    ForecastDataType,
)
from .common import (
    # Enums
    UserTypeEnum,
    VerificationStatusEnum,
    OnboardingStatusEnum,
    ExpertiseAreaEnum,
    DocumentTypeEnum,
    VideoKYCStatusEnum,
    PortfolioStatusEnum,
    OrganizationTypeEnum,
    ConsultationTypeEnum,
    DurationEnum,
    PaymentTypeEnum,
    DigitalWalletEnum,
    PaymentStatusEnum,
    NotificationChannelEnum,
    NotificationStatusEnum,
    # NotificationTemplateTypeEnum,  # Commented out until implemented
    
    # # Notification Types  # Commented out until implemented
    # NotificationTemplateType,
    # NotificationType,
    
    # Response Types
    SuccessResponseType,
    AuthPayloadType,
    ValidationErrorType,
    ErrorResponseType,
    
    # Pagination Types
    PageInfoType,
    PaginationInputType,
    
    # Search and Filter Types
    SearchInputType,
    SortInputType,
    
    # Analytics Types
    ProfessionalStatsType,
    ClientStatsType,
    
    # File Upload Types
    FileUploadType,
    FileInputType,
)

__all__ = [
    # User Types
    'UserType',
    'ClientProfileType', 
    'ProfessionalProfileType',  # Now from proffesional_profile.py
    'ProfessionalPricingType',
    'ProfessionalReviewSummaryType',
    'PasswordResetTokenType',
    'UserInputType',
    'ClientProfileInputType',
    'ProfessionalProfileInputType',
    
    # Professional Profile Types
    'ProfessionalDocumentType',
    'VideoKYCType',
    'PortfolioType',
    'ConsultationAvailabilityType',
    'PaymentMethodType',
    'OnboardingProgressType',
    'ProfessionalSettingsType',
    'ProfessionalDocumentInputType',
    'VideoKYCInputType',
    'PortfolioInputType',
    'ConsultationAvailabilityInputType',
    'PaymentMethodInputType',
    'ProfessionalSettingsInputType',
    
    # Common Types - Enums
    'UserTypeEnum',
    'VerificationStatusEnum',
    'OnboardingStatusEnum',
    'ExpertiseAreaEnum',
    'DocumentTypeEnum',
    'VideoKYCStatusEnum',
    'PortfolioStatusEnum',
    'OrganizationTypeEnum',
    'ConsultationTypeEnum',
    'DurationEnum',
    'PaymentTypeEnum',
    'DigitalWalletEnum',
    'NotificationChannelEnum',
    'NotificationStatusEnum',
    # 'NotificationTemplateTypeEnum',  # Commented out until implemented
    
    # # Common Types - Notifications  # Commented out until implemented
    # 'NotificationTemplateType',
    # 'NotificationType',
    
    # Common Types - Response Types
    'SuccessResponseType',
    'AuthPayloadType',
    'ValidationErrorType',
    'ErrorResponseType',
    
    # Common Types - Pagination
    'PageInfoType',
    'PaginationInputType',
    
    # Common Types - Search and Filter
    'SearchInputType',
    'SortInputType',
    
    # Common Types - Analytics
    'ProfessionalStatsType',
    'ClientStatsType',
    
    # Analytics Types
    'ProfessionalAnalyticsType',
    'ClientAnalyticsType',
    'PlatformAnalyticsType',
    'RevenueAnalyticsType',
    'UserEngagementAnalyticsType',
    'PerformanceMetricsType',
    'AnalyticsFilterInputType',
    'RevenueFilterInputType',
    'PerformanceFilterInputType',
    'PeriodComparisonType',
    'BenchmarkComparisonType',
    'ForecastDataType',
    'SeasonalityAnalysisType',
    
    # Common Types - File Upload
    'FileUploadType',
    'FileInputType',
]
