import re
import phonenumbers
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Optional
import magic


def validate_email_format(email: str) -> bool:
    """
    Validate email format using Django's built-in validator
    """
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def validate_phone_number(phone: str, country_code: str = 'IN') -> dict:
    """
    Validate phone number format using phonenumbers library
    
    Args:
        phone: Phone number string
        country_code: ISO country code (default: 'IN' for India)
    
    Returns:
        dict: Validation result with is_valid, formatted, and type
    """
    try:
        parsed = phonenumbers.parse(phone, country_code)
        is_valid = phonenumbers.is_valid_number(parsed)
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        number_type = phonenumbers.number_type(parsed)
        
        return {
            'is_valid': is_valid,
            'formatted': formatted,
            'type': str(number_type),
            'country': phonenumbers.geocoder.description_for_number(parsed, 'en')
        }
    except phonenumbers.NumberParseException:
        return {
            'is_valid': False,
            'formatted': None,
            'type': None,
            'country': None
        }


def validate_file_type(file, allowed_types: List[str]) -> bool:
    """
    Validate file type using file content (not just extension)
    
    Args:
        file: File object
        allowed_types: List of allowed MIME types
    
    Returns:
        bool: True if file type is allowed
    """
    try:
        file_content = file.read(1024)  # Read first 1KB
        file.seek(0)  # Reset file pointer
        
        mime_type = magic.from_buffer(file_content, mime=True)
        return mime_type in allowed_types
    except Exception:
        return False


def validate_file_size(file, max_size_mb: int = 10) -> bool:
    """
    Validate file size
    
    Args:
        file: File object
        max_size_mb: Maximum file size in MB
    
    Returns:
        bool: True if file size is within limit
    """
    try:
        file_size = file.size
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    except Exception:
        return False


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength
    
    Returns:
        dict: Validation result with strength score and feedback
    """
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password must be at least 8 characters long")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Password must contain at least one uppercase letter")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Password must contain at least one lowercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Password must contain at least one number")
    
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
        score += 1
    else:
        feedback.append("Password must contain at least one special character")
    
    # Check for common patterns
    common_patterns = [
        r'12345',
        r'password',
        r'qwerty',
        r'abc123'
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            score -= 1
            feedback.append("Password contains common patterns")
            break
    
    strength_levels = {
        0: "Very Weak",
        1: "Weak", 
        2: "Fair",
        3: "Good",
        4: "Strong",
        5: "Very Strong"
    }
    
    return {
        'score': max(0, score),
        'strength': strength_levels.get(max(0, score), "Very Weak"),
        'is_strong': score >= 4,
        'feedback': feedback
    }


def validate_professional_license(license_number: str, license_type: str = 'bar') -> dict:
    """
    Validate professional license number format
    
    Args:
        license_number: License number string
        license_type: Type of license (bar, medical, etc.)
    
    Returns:
        dict: Validation result
    """
    # Basic validation patterns for different license types
    patterns = {
        'bar': r'^[A-Z]{2}[0-9]{4,8}$',  # Example: KA123456
        'medical': r'^[0-9]{4,10}$',
        'ca': r'^[0-9]{6}$'  # Chartered Accountant
    }
    
    pattern = patterns.get(license_type.lower(), r'^[A-Z0-9]{4,12}$')
    
    is_valid = bool(re.match(pattern, license_number.upper()))
    
    return {
        'is_valid': is_valid,
        'formatted': license_number.upper() if is_valid else license_number,
        'type': license_type
    }


def validate_consultation_time(consultation_date: datetime, duration_minutes: int = 60) -> dict:
    """
    Validate consultation booking time
    
    Args:
        consultation_date: Proposed consultation datetime
        duration_minutes: Duration in minutes
    
    Returns:
        dict: Validation result
    """
    now = timezone.now()
    errors = []
    
    # Check if date is in the future
    if consultation_date <= now:
        errors.append("Consultation date must be in the future")
    
    # Check if date is too far in advance (e.g., 6 months)
    max_advance = now + timedelta(days=180)
    if consultation_date > max_advance:
        errors.append("Consultation date cannot be more than 6 months in advance")
    
    # Check minimum advance booking time (e.g., 2 hours)
    min_advance = now + timedelta(hours=2)
    if consultation_date < min_advance:
        errors.append("Consultation must be booked at least 2 hours in advance")
    
    # Check business hours (9 AM to 9 PM)
    consultation_hour = consultation_date.hour
    if consultation_hour < 9 or consultation_hour > 21:
        errors.append("Consultations are only available between 9 AM and 9 PM")
    
    # Check duration
    if duration_minutes < 30 or duration_minutes > 180:
        errors.append("Consultation duration must be between 30 and 180 minutes")
    
    # Check if it's a weekend (if needed)
    if consultation_date.weekday() > 4:  # Saturday = 5, Sunday = 6
        # This could be configurable per professional
        pass
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'consultation_date': consultation_date,
        'end_time': consultation_date + timedelta(minutes=duration_minutes)
    }


def validate_payment_details(payment_type: str, payment_data: dict) -> dict:
    """
    Validate payment method details
    
    Args:
        payment_type: Type of payment (bank_account, digital_wallet)
        payment_data: Payment details dictionary
    
    Returns:
        dict: Validation result
    """
    errors = []
    
    if payment_type == 'BANK_ACCOUNT':
        required_fields = ['account_holder_name', 'bank_name', 'account_number', 'ifsc_code']
        
        for field in required_fields:
            if not payment_data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        # Validate IFSC code format (Indian banks)
        ifsc_code = payment_data.get('ifsc_code', '')
        if ifsc_code and not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc_code):
            errors.append("Invalid IFSC code format")
        
        # Validate account number
        account_number = payment_data.get('account_number', '')
        if account_number and not re.match(r'^[0-9]{9,18}$', account_number):
            errors.append("Account number must be 9-18 digits")
    
    elif payment_type == 'DIGITAL_WALLET':
        wallet_provider = payment_data.get('wallet_provider')
        if not wallet_provider:
            errors.append("Wallet provider is required")
        
        # Validate based on wallet provider
        if wallet_provider in ['PAYTM', 'GOOGLE_PAY', 'PHONEPE']:
            phone = payment_data.get('wallet_phone_number')
            if not phone:
                errors.append("Phone number is required for this wallet")
            else:
                phone_validation = validate_phone_number(phone)
                if not phone_validation['is_valid']:
                    errors.append("Invalid phone number format")
        
        elif wallet_provider == 'PAYPAL':
            email = payment_data.get('wallet_email')
            if not email:
                errors.append("Email is required for PayPal")
            elif not validate_email_format(email):
                errors.append("Invalid email format")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'payment_type': payment_type,
        'validated_data': payment_data
    }
