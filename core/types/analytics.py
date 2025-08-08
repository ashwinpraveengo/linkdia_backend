import graphene
from graphene_django import DjangoObjectType
from django.db.models import Sum, Avg, Count
from decimal import Decimal
from typing import Dict, Any
from core.models import (
    ProfessionalProfile,
    CustomUser
)


class ProfessionalAnalyticsType(graphene.ObjectType):
    """Analytics data for professional dashboard"""
    total_consultations = graphene.Int()
    total_earnings = graphene.Decimal()
    average_rating = graphene.Float()
    total_reviews = graphene.Int()
    completion_rate = graphene.Float()
    response_time_avg = graphene.String()
    
    # Monthly stats
    this_month_bookings = graphene.Int()
    this_month_earnings = graphene.Decimal()
    this_month_reviews = graphene.Int()
    
    # Growth metrics
    bookings_growth = graphene.Float()  # percentage change from last month
    earnings_growth = graphene.Float()
    rating_trend = graphene.Float()
    
    # Consultation type breakdown
    online_consultations = graphene.Int()
    offline_consultations = graphene.Int()
    
    # Time-based analytics
    peak_hours = graphene.List(graphene.String)
    popular_days = graphene.List(graphene.String)
    
    # Client analytics
    repeat_clients = graphene.Int()
    new_clients = graphene.Int()
    client_satisfaction = graphene.Float()


class ClientAnalyticsType(graphene.ObjectType):
    """Analytics data for client dashboard"""
    total_bookings = graphene.Int()
    total_spent = graphene.Decimal()
    favorite_professionals = graphene.List(graphene.ID)
    consultation_history_count = graphene.Int()
    
    # Spending breakdown
    this_month_spent = graphene.Decimal()
    avg_consultation_cost = graphene.Decimal()
    
    # Consultation preferences
    preferred_consultation_type = graphene.String()
    most_used_expertise_area = graphene.String()
    
    # Review statistics
    reviews_given = graphene.Int()
    avg_rating_given = graphene.Float()


class PlatformAnalyticsType(graphene.ObjectType):
    """Overall platform analytics (admin only)"""
    total_users = graphene.Int()
    total_professionals = graphene.Int()
    total_clients = graphene.Int()
    verified_professionals = graphene.Int()
    
    # Booking statistics
    total_bookings = graphene.Int()
    completed_bookings = graphene.Int()
    cancelled_bookings = graphene.Int()
    booking_completion_rate = graphene.Float()
    
    # Financial metrics
    total_platform_revenue = graphene.Decimal()
    total_professional_earnings = graphene.Decimal()
    avg_booking_value = graphene.Decimal()
    
    # Growth metrics
    monthly_user_growth = graphene.Float()
    monthly_booking_growth = graphene.Float()
    monthly_revenue_growth = graphene.Float()
    
    # Popular metrics
    most_popular_expertise_areas = graphene.List(graphene.String)
    top_performing_professionals = graphene.List(graphene.ID)
    busiest_time_slots = graphene.List(graphene.String)


class RevenueAnalyticsType(graphene.ObjectType):
    """Revenue analytics breakdown"""
    period = graphene.String()  # daily, weekly, monthly, yearly
    total_revenue = graphene.Decimal()
    platform_fee_collected = graphene.Decimal()
    professional_payouts = graphene.Decimal()
    refunds_processed = graphene.Decimal()
    net_revenue = graphene.Decimal()
    
    # Revenue by category
    online_consultation_revenue = graphene.Decimal()
    offline_consultation_revenue = graphene.Decimal()
    
    # Payment method breakdown
    credit_card_revenue = graphene.Decimal()
    digital_wallet_revenue = graphene.Decimal()
    bank_transfer_revenue = graphene.Decimal()


class BookingAnalyticsType(graphene.ObjectType):
    """Booking pattern analytics"""
    period = graphene.String()
    total_bookings = graphene.Int()
    successful_bookings = graphene.Int()
    cancelled_bookings = graphene.Int()
    no_show_bookings = graphene.Int()
    
    # Timing analytics
    peak_booking_hours = graphene.List(graphene.String)
    popular_booking_days = graphene.List(graphene.String)
    avg_advance_booking_time = graphene.String()  # how far in advance bookings are made
    
    # Duration analytics
    avg_consultation_duration = graphene.Int()  # in minutes
    most_popular_duration = graphene.Int()
    
    # Type preferences
    online_booking_percentage = graphene.Float()
    offline_booking_percentage = graphene.Float()


class UserEngagementAnalyticsType(graphene.ObjectType):
    """User engagement and retention analytics"""
    daily_active_users = graphene.Int()
    weekly_active_users = graphene.Int()
    monthly_active_users = graphene.Int()
    
    # Retention metrics
    user_retention_rate = graphene.Float()  # percentage of users who return
    avg_session_duration = graphene.String()
    avg_sessions_per_user = graphene.Float()
    
    # Professional engagement
    active_professionals = graphene.Int()
    avg_consultations_per_professional = graphene.Float()
    professional_response_rate = graphene.Float()
    
    # Client engagement
    active_clients = graphene.Int()
    repeat_booking_rate = graphene.Float()
    client_satisfaction_score = graphene.Float()


class PerformanceMetricsType(graphene.ObjectType):
    """System performance metrics"""
    avg_response_time = graphene.Float()  # API response time in ms
    uptime_percentage = graphene.Float()
    error_rate = graphene.Float()
    
    # Booking system performance
    booking_success_rate = graphene.Float()
    payment_success_rate = graphene.Float()
    notification_delivery_rate = graphene.Float()
    
    # User experience metrics
    page_load_time = graphene.Float()
    search_response_time = graphene.Float()
    video_call_connection_rate = graphene.Float()


# Input types for analytics queries
class AnalyticsFilterInputType(graphene.InputObjectType):
    """Input type for filtering analytics data"""
    start_date = graphene.Date()
    end_date = graphene.Date()
    period = graphene.String()  # daily, weekly, monthly, yearly
    professional_id = graphene.ID()
    client_id = graphene.ID()
    expertise_area = graphene.String()
    consultation_type = graphene.String()
    location = graphene.String()


class RevenueFilterInputType(graphene.InputObjectType):
    """Input type for revenue analytics filtering"""
    start_date = graphene.Date()
    end_date = graphene.Date()
    period = graphene.String()
    payment_method = graphene.String()
    currency = graphene.String()
    min_amount = graphene.Decimal()
    max_amount = graphene.Decimal()


class PerformanceFilterInputType(graphene.InputObjectType):
    """Input type for performance metrics filtering"""
    start_date = graphene.Date()
    end_date = graphene.Date()
    metric_type = graphene.String()  # response_time, uptime, error_rate
    threshold = graphene.Float()


# Comparison types for period-over-period analytics
class PeriodComparisonType(graphene.ObjectType):
    """Compare metrics between two periods"""
    current_period = graphene.Field(ProfessionalAnalyticsType)
    previous_period = graphene.Field(ProfessionalAnalyticsType)
    growth_percentage = graphene.Float()
    trend = graphene.String()  # increasing, decreasing, stable


class BenchmarkComparisonType(graphene.ObjectType):
    """Compare individual metrics against platform benchmarks"""
    user_metric = graphene.Float()
    platform_average = graphene.Float()
    percentile_rank = graphene.Float()
    performance_category = graphene.String()  # excellent, good, average, below_average


# Forecast types
class ForecastDataType(graphene.ObjectType):
    """Forecasted analytics data"""
    period = graphene.String()
    forecasted_bookings = graphene.Int()
    forecasted_revenue = graphene.Decimal()
    confidence_interval = graphene.Float()
    trend_direction = graphene.String()  # upward, downward, stable


class SeasonalityAnalysisType(graphene.ObjectType):
    """Seasonal pattern analysis"""
    season = graphene.String()  # spring, summer, fall, winter
    booking_pattern = graphene.String()  # high, medium, low
    revenue_impact = graphene.Float()  # percentage impact on revenue
    recommended_actions = graphene.List(graphene.String)
