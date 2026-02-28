"""
Helper functions for subscription management.
Import these where needed in your app.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.subscription_model import SubscriptionModel
from utils.enums import SubscriptionStatus

def calculate_days_remaining(subscription: SubscriptionModel) -> int:
    """Calculate days remaining in current subscription period"""
    now = datetime.utcnow()
    days_left = (subscription.subscription_end_date - now).days
    return max(0, days_left)

def is_subscription_active(subscription: SubscriptionModel) -> bool:
    """Check if subscription allows feature access"""
    if not subscription:
        return False
    
    active_statuses = [
        SubscriptionStatus.TRIAL,
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.GRACE_PERIOD
    ]
    
    if subscription.subscription_status in active_statuses:
        return True
    
    # Check cancelled subscriptions that are still within paid period
    if subscription.subscription_status == SubscriptionStatus.CANCELLED:
        now = datetime.utcnow()
        return now <= subscription.subscription_end_date
    
    return False

def get_subscription_message(subscription: SubscriptionModel) -> str:
    """Get user-friendly message about subscription status"""
    if not subscription:
        return "No active subscription. Start your free trial today!"
    
    days_left = calculate_days_remaining(subscription)
    
    if subscription.subscription_status == SubscriptionStatus.TRIAL:
        return f"Trial active. {days_left} days remaining."
    
    elif subscription.subscription_status == SubscriptionStatus.ACTIVE:
        return f"Subscription active. {days_left} days remaining."
    
    elif subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
        grace_number = subscription.grace_periods_used
        return f"Grace period {grace_number}/2. Please update payment. {days_left} days remaining."
    
    elif subscription.subscription_status == SubscriptionStatus.EXPIRED:
        return "Subscription expired. Renew to restore full access."
    
    elif subscription.subscription_status == SubscriptionStatus.CANCELLED:
        if datetime.utcnow() <= subscription.subscription_end_date:
            return f"Subscription cancelled but active until {subscription.subscription_end_date.strftime('%B %d, %Y')}."
        else:
            return "Subscription ended. Renew to restore access."
    
    return "Unknown subscription status."

def should_show_payment_prompt(subscription: SubscriptionModel) -> bool:
    """Determine if payment prompt should be shown"""
    if not subscription:
        return False
    
    # Show prompt in grace periods
    if subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
        return True
    
    # Show prompt 3 days before trial ends
    if subscription.subscription_status == SubscriptionStatus.TRIAL:
        days_left = calculate_days_remaining(subscription)
        return days_left <= 3
    
    # Show prompt 7 days before active subscription ends
    if subscription.subscription_status == SubscriptionStatus.ACTIVE:
        days_left = calculate_days_remaining(subscription)
        return days_left <= 7
    
    return False

def get_payment_prompt_urgency(subscription: SubscriptionModel) -> str:
    """Get urgency level for payment prompts"""
    if not subscription:
        return "none"
    
    days_left = calculate_days_remaining(subscription)
    
    if subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
        if subscription.grace_periods_used == 2:
            return "critical"  # Last grace period
        return "high"  # First grace period
    
    if subscription.subscription_status == SubscriptionStatus.TRIAL:
        if days_left <= 1:
            return "high"
        if days_left <= 3:
            return "medium"
        return "low"
    
    if subscription.subscription_status == SubscriptionStatus.ACTIVE:
        if days_left <= 3:
            return "medium"
        if days_left <= 7:
            return "low"
    
    return "none"

def can_create_meal_plan(subscription: SubscriptionModel) -> bool:
    """Check if user can create new meal plans"""
    # Expired users can only view, not create
    if subscription and subscription.subscription_status == SubscriptionStatus.EXPIRED:
        return False
    
    return is_subscription_active(subscription)

def can_edit_meal_plan(subscription: SubscriptionModel) -> bool:
    """Check if user can edit meal plans"""
    # Same logic as create
    return can_create_meal_plan(subscription)

def can_receive_alerts(subscription: SubscriptionModel) -> bool:
    """Check if user should receive meal alerts/reminders"""
    # Expired users don't get alerts
    if subscription and subscription.subscription_status == SubscriptionStatus.EXPIRED:
        return False
    
    return is_subscription_active(subscription)

def get_feature_access_summary(subscription: SubscriptionModel) -> dict:
    """Get complete feature access summary for user"""
    if not subscription:
        return {
            "has_subscription": False,
            "can_create_meal_plans": False,
            "can_edit_meal_plans": False,
            "can_receive_alerts": False,
            "can_view_meal_plans": False,
            "show_payment_prompt": True,
            "payment_urgency": "critical",
            "message": "No subscription. Start your free trial!"
        }
    
    is_active = is_subscription_active(subscription)
    is_expired = subscription.subscription_status == SubscriptionStatus.EXPIRED
    
    return {
        "has_subscription": True,
        "subscription_status": subscription.subscription_status.value,
        "can_create_meal_plans": can_create_meal_plan(subscription),
        "can_edit_meal_plans": can_edit_meal_plan(subscription),
        "can_receive_alerts": can_receive_alerts(subscription),
        "can_view_meal_plans": True,  # Always allow viewing
        "days_remaining": calculate_days_remaining(subscription),
        "show_payment_prompt": should_show_payment_prompt(subscription),
        "payment_urgency": get_payment_prompt_urgency(subscription),
        "message": get_subscription_message(subscription)
    }

def get_user_subscription(db: Session, user_id: str) -> SubscriptionModel:
    """Helper to get user's subscription"""
    return db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == user_id
    ).first()

# Example usage in your controllers:
"""
from utils.subscription_helpers import get_feature_access_summary, get_user_subscription

def some_endpoint(user_id: str, db: Session):
    subscription = get_user_subscription(db, user_id)
    access = get_feature_access_summary(subscription)
    
    if not access['can_create_meal_plans']:
        return {
            "status": "error",
            "message": "Subscription required to create meal plans",
            "subscription_info": access
        }
    
    # Proceed with creating meal plan...
"""