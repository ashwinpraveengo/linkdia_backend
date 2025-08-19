import uuid
import secrets
import string
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import QuerySet, Q
from django.conf import settings
import re
import hashlib


def generate_unique_filename(original_filename: str, prefix: str = '') -> str:
    """
    Generate a unique filename while preserving the extension
    
    Args:
        original_filename: Original file name
        prefix: Optional prefix for the filename
    
    Returns:
        str: Unique filename
    """
    # Extract file extension
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        ext = f".{ext}"
    else:
        name = original_filename
        ext = ""
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Combine parts
    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}{ext}"
    else:
        filename = f"{timestamp}_{unique_id}{ext}"
    
    # Sanitize filename
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    return filename


def format_currency(amount: Decimal, currency: str = 'INR', locale: str = 'en_IN') -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale for formatting
    
    Returns:
        str: Formatted currency string
    """
    try:
        if currency == 'INR':
            # Indian Rupee formatting
            amount_str = f"₹{amount:,.2f}"
            return amount_str
        elif currency == 'USD':
            return f"${amount:,.2f}"
        elif currency == 'EUR':
            return f"€{amount:,.2f}"
        else:
            return f"{currency} {amount:,.2f}"
    except Exception:
        return str(amount)


def calculate_consultation_fee(
    hourly_rate: Decimal,
    duration_minutes: int,
    discount_percentage: Decimal = Decimal('0'),
    platform_fee_percentage: Decimal = Decimal('2.5')
) -> Dict[str, Decimal]:
    """
    Calculate consultation fee breakdown
    
    Args:
        hourly_rate: Professional's hourly rate
        duration_minutes: Consultation duration in minutes
        discount_percentage: Discount percentage to apply
        platform_fee_percentage: Platform fee percentage
    
    Returns:
        dict: Fee breakdown
    """
    # Convert duration to hours
    duration_hours = Decimal(duration_minutes) / Decimal('60')
    
    # Calculate base amount
    base_amount = hourly_rate * duration_hours
    
    # Apply discount
    discount_amount = base_amount * (discount_percentage / Decimal('100'))
    amount_after_discount = base_amount - discount_amount
    
    # Calculate platform fee
    platform_fee = amount_after_discount * (platform_fee_percentage / Decimal('100'))
    
    # Final amounts
    total_amount = amount_after_discount
    professional_amount = amount_after_discount - platform_fee
    
    return {
        'base_amount': base_amount.quantize(Decimal('0.01')),
        'discount_amount': discount_amount.quantize(Decimal('0.01')),
        'platform_fee': platform_fee.quantize(Decimal('0.01')),
        'total_amount': total_amount.quantize(Decimal('0.01')),
        'professional_amount': professional_amount.quantize(Decimal('0.01')),
        'duration_hours': duration_hours
    }


def get_time_slots(
    start_time: time,
    end_time: time,
    slot_duration: int = 60,
    buffer_time: int = 15,
    excluded_times: List[Tuple[time, time]] = None
) -> List[Dict[str, time]]:
    """
    Generate available time slots for a given time range
    
    Args:
        start_time: Start time
        end_time: End time
        slot_duration: Slot duration in minutes
        buffer_time: Buffer time between slots in minutes
        excluded_times: List of excluded time ranges
    
    Returns:
        list: Available time slots
    """
    slots = []
    excluded_times = excluded_times or []
    
    # Convert times to datetime for easier calculation
    today = timezone.now().date()
    current_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    
    slot_delta = timedelta(minutes=slot_duration)
    buffer_delta = timedelta(minutes=buffer_time)
    total_slot_time = slot_delta + buffer_delta
    
    while current_datetime + slot_delta <= end_datetime:
        slot_start = current_datetime.time()
        slot_end = (current_datetime + slot_delta).time()
        
        # Check if slot overlaps with excluded times
        slot_available = True
        for exc_start, exc_end in excluded_times:
            if not (slot_end <= exc_start or slot_start >= exc_end):
                slot_available = False
                break
        
        if slot_available:
            slots.append({
                'start_time': slot_start,
                'end_time': slot_end,
                'duration_minutes': slot_duration
            })
        
        current_datetime += total_slot_time
    
    return slots


def parse_availability(availability_string: str) -> Dict[str, List[Tuple[time, time]]]:
    """
    Parse availability string into structured format
    
    Format: "MON:09:00-17:00,TUE:10:00-18:00"
    
    Args:
        availability_string: Comma-separated availability string
    
    Returns:
        dict: Parsed availability by day
    """
    availability = {}
    
    if not availability_string:
        return availability
    
    day_mappings = {
        'MON': 'monday', 'TUE': 'tuesday', 'WED': 'wednesday',
        'THU': 'thursday', 'FRI': 'friday', 'SAT': 'saturday', 'SUN': 'sunday'
    }
    
    for day_schedule in availability_string.split(','):
        if ':' not in day_schedule:
            continue
        
        day_code, time_range = day_schedule.split(':', 1)
        day_name = day_mappings.get(day_code.upper())
        
        if not day_name or '-' not in time_range:
            continue
        
        try:
            start_str, end_str = time_range.split('-')
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
            
            if day_name not in availability:
                availability[day_name] = []
            
            availability[day_name].append((start_time, end_time))
        except ValueError:
            continue
    
    return availability


def generate_meeting_id(length: int = 10) -> str:
    """
    Generate a random meeting ID
    
    Args:
        length: Length of the meeting ID
    
    Returns:
        str: Random meeting ID
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def sanitize_input(input_string: str, max_length: int = None) -> str:
    """
    Sanitize user input string
    
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not input_string:
        return ""
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]+>', '', input_string)
    
    # Remove extra whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    return sanitized


def paginate_queryset(
    queryset: QuerySet,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict:
    """
    Paginate a Django queryset
    
    Args:
        queryset: Django queryset to paginate
        page: Page number
        per_page: Items per page
        max_per_page: Maximum items per page allowed
    
    Returns:
        dict: Pagination result
    """
    # Limit per_page to maximum allowed
    per_page = min(per_page, max_per_page)
    
    paginator = Paginator(queryset, per_page)
    
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)
    
    return {
        'objects': page_obj.object_list,
        'page_info': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'per_page': per_page,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    }


def search_professionals(
    query: str = None,
    location: str = None,
    expertise_area: str = None,
    min_rating: float = None,
    max_rate: Decimal = None,
    is_available: bool = True
) -> QuerySet:
    """
    Search and filter professionals
    
    Args:
        query: Search query for name/bio
        location: Location filter
        expertise_area: Area of expertise
        min_rating: Minimum rating
        max_rate: Maximum hourly rate
        is_available: Filter by availability
    
    Returns:
        QuerySet: Filtered professionals
    """
    from core.models import ProfessionalProfile
    
    queryset = ProfessionalProfile.objects.filter(
        verification_status='VERIFIED',
        onboarding_completed=True
    )
    
    if is_available:
        queryset = queryset.filter(is_available=True)
    
    if query:
        queryset = queryset.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(bio_introduction__icontains=query) |
            Q(specialization__icontains=query)
        )
    
    if location:
        queryset = queryset.filter(location__icontains=location)
    
    if expertise_area:
        queryset = queryset.filter(area_of_expertise=expertise_area)
    
    if min_rating:
        queryset = queryset.filter(average_rating__gte=min_rating)
    
    if max_rate:
        queryset = queryset.filter(availability__hourly_rate__lte=max_rate)
    
    return queryset.distinct()


def filter_by_availability(
    professionals_queryset: QuerySet,
    date: datetime.date = None,
    start_time: time = None,
    duration_minutes: int = 60
) -> QuerySet:
    """
    Filter professionals by availability on a specific date/time
    
    Args:
        professionals_queryset: QuerySet of professionals
        date: Date to check availability
        start_time: Start time to check
        duration_minutes: Required duration
    
    Returns:
        QuerySet: Professionals available at the specified time
    """
    if not date:
        date = timezone.now().date()
    
    if not start_time:
        return professionals_queryset
    
    # Get day of week
    day_of_week = date.weekday()  # 0 = Monday
    day_fields = {
        0: 'monday', 1: 'tuesday', 2: 'wednesday',
        3: 'thursday', 4: 'friday', 5: 'saturday', 6: 'sunday'
    }
    day_field = day_fields[day_of_week]
    
    # Calculate end time
    end_time = (datetime.combine(date, start_time) + 
                timedelta(minutes=duration_minutes)).time()
    
    # Filter by availability
    available_professionals = professionals_queryset.filter(
        **{f'availability__{day_field}': True},
        availability__start_time__lte=start_time,
        availability__end_time__gte=end_time,
        availability__is_active=True
    )
    
    return available_professionals


def generate_hash(text: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash for a given text
    
    Args:
        text: Text to hash
        algorithm: Hashing algorithm (md5, sha1, sha256)
    
    Returns:
        str: Hash string
    """
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    else:  # default to sha256
        return hashlib.sha256(text.encode()).hexdigest()


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    Mask sensitive data (like account numbers, phone numbers)
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
    
    Returns:
        str: Masked data
    """
    if not data or len(data) <= visible_chars:
        return data
    
    masked_part = mask_char * (len(data) - visible_chars)
    visible_part = data[-visible_chars:]
    
    return masked_part + visible_part

import hashlib

def generate_slot_id(professional_id, start_time, end_time):
    """
    Generate a stable unique slot ID using professional + start + end.
    """
    raw = f"{professional_id}-{start_time.isoformat()}-{end_time.isoformat()}"
    return hashlib.md5(raw.encode()).hexdigest()
