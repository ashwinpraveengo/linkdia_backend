from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CustomUser, PasswordResetToken, ClientProfile, ProfessionalProfile,
    ProfessionalDocument, VideoKYC, Portfolio, ConsultationAvailability,
    PaymentMethod, ProfessionalPricing, ConsultationSlot
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active', 'date_joined', 'is_google_user')
    list_filter = ('is_staff', 'is_active', 'user_type', 'is_google_user', 'is_email_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Profile Picture', {'fields': ('profile_picture_name', 'profile_picture_content_type', 'profile_picture_size')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Google OAuth', {'fields': ('google_id', 'is_google_user')}),
        ('Verification', {'fields': ('is_email_verified',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('profile_picture_data',)



@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'is_used', 'is_expired_display')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')
    
    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.short_description = 'Is Expired'
    is_expired_display.boolean = True


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'location', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'company_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'area_of_expertise', 'years_of_experience', 'verification_status', 'onboarding_step', 'onboarding_completed')
    list_filter = ('area_of_expertise', 'verification_status', 'onboarding_step', 'onboarding_completed', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'location')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {'fields': ('user',)}),
        ('Professional Details', {'fields': ('area_of_expertise', 'years_of_experience', 'bio_introduction', 'location')}),
        ('Status', {'fields': ('verification_status', 'onboarding_step', 'onboarding_completed')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ProfessionalDocument)
class ProfessionalDocumentAdmin(admin.ModelAdmin):
    list_display = ('professional', 'document_type', 'document_name', 'verification_status', 'uploaded_at', 'file_size_display')
    list_filter = ('document_type', 'verification_status', 'uploaded_at')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name', 'document_name')
    readonly_fields = ('id', 'uploaded_at', 'verified_at', 'document_data')
    
    def file_size_display(self, obj):
        if obj.document_size:
            return f"{obj.document_size / 1024:.1f} KB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(VideoKYC)
class VideoKYCAdmin(admin.ModelAdmin):
    list_display = ('professional', 'status', 'completed_at', 'verified_at', 'created_at')
    list_filter = ('status', 'completed_at', 'verified_at', 'created_at')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name')
    readonly_fields = ('id', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('professional', 'name', 'document_name', 'file_size_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name', 'name')
    readonly_fields = ('id', 'created_at', 'document_data')
    
    def file_size_display(self, obj):
        if obj.document_size:
            return f"{obj.document_size / 1024:.1f} KB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(ConsultationAvailability)
class ConsultationAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('professional', 'available_days_display', 'from_time', 'to_time', 'consultation_type', 'consultation_duration_minutes')
    list_filter = ('consultation_type', 'consultation_duration_minutes', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Professional', {'fields': ('professional',)}),
        ('Available Days', {'fields': ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')}),
        ('Time Settings', {'fields': ('from_time', 'to_time', 'consultation_duration_minutes')}),
        ('Consultation Type', {'fields': ('consultation_type',)}),
        ('Calendar Integration', {'fields': ('google_calendar_sync', 'outlook_calendar_sync')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def available_days_display(self, obj):
        days = obj.get_available_days()
        return ', '.join(days) if days else 'No days selected'
    available_days_display.short_description = 'Available Days'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('professional', 'payment_type', 'payment_details_display', 'created_at')
    list_filter = ('payment_type', 'wallet_provider', 'created_at')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name', 'account_holder_name', 'bank_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Professional', {'fields': ('professional',)}),
        ('Payment Type', {'fields': ('payment_type',)}),
        ('Bank Account Details', {'fields': ('account_holder_name', 'bank_name', 'account_number', 'ifsc_code')}),
        ('Digital Wallet Details', {'fields': ('wallet_provider', 'wallet_phone_number')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def payment_details_display(self, obj):
        if obj.payment_type == 'BANK_ACCOUNT':
            return f"{obj.bank_name} - {obj.account_number[-4:] if obj.account_number else 'N/A'}"
        else:
            return f"{obj.get_wallet_provider_display()} - {obj.wallet_phone_number}"
    payment_details_display.short_description = 'Payment Details'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(ProfessionalPricing)
class ProfessionalPricingAdmin(admin.ModelAdmin):
    list_display = ('professional', 'fee_30_min', 'fee_60_min', 'fee_90_min', 'fee_120_min', 'accepts_online', 'accepts_offline')
    list_filter = ('accepts_online', 'accepts_offline', 'created_at')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Professional', {'fields': ('professional',)}),
        ('Consultation Fees', {'fields': ('fee_30_min', 'fee_60_min', 'fee_90_min', 'fee_120_min')}),
        ('Additional Charges', {'fields': ('offline_consultation_extra',)}),
        ('Consultation Types', {'fields': ('accepts_online', 'accepts_offline')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user')


@admin.register(ConsultationSlot)
class ConsultationSlotAdmin(admin.ModelAdmin):
    list_display = ('professional', 'start_time', 'end_time', 'status', 'custom_rate', 'held_by', 'held_until')
    list_filter = ('status', 'start_time', 'created_at')
    search_fields = ('professional__user__email', 'professional__user__first_name', 'professional__user__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Slot Details', {'fields': ('professional', 'start_time', 'end_time', 'status')}),
        ('Pricing', {'fields': ('custom_rate',)}),
        ('Hold Information', {'fields': ('held_by', 'held_until')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('professional__user', 'held_by')

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'BOOKED':
            readonly.extend(['professional', 'start_time', 'end_time'])
        return readonly
