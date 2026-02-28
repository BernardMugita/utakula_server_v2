from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session
from connect import SessionLocal

from controllers.subscription_controller import SubscriptionController
from schemas.subscription_schema import (
    SubscriptionCreate, SubscriptionUpgrade, SubscriptionCancel, SubscriptionStatusCheck,
    SubscriptionStatusResponse, CreateSubscriptionResponse, RetrieveSubscriptionResponse,
    UpdateSubscriptionResponse, CancelSubscriptionResponse
)

router = APIRouter()
subscription_controller = SubscriptionController()

def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/subscriptions/start_trial", response_model=CreateSubscriptionResponse)
async def start_trial(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """
    Start 14-day free trial for new user.
    Called automatically on user signup.
    """
    return subscription_controller.start_trial(subscription_data, db, authorization)

@router.post("/subscriptions/check_status", response_model=SubscriptionStatusResponse)
async def check_subscription_status(
    user_data: SubscriptionStatusCheck = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """
    Check user's subscription status and feature access.
    Call this on app launch and before accessing premium features.
    """
    return subscription_controller.check_subscription_status(user_data, db, authorization)

@router.post("/subscriptions/get_user_subscription", response_model=RetrieveSubscriptionResponse)
async def get_user_subscription(
    user_data: SubscriptionStatusCheck = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get detailed subscription info for user"""
    return subscription_controller.get_user_subscription(user_data, db, authorization)

@router.post("/subscriptions/upgrade", response_model=UpdateSubscriptionResponse)
async def upgrade_subscription(
    upgrade_data: SubscriptionUpgrade,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Upgrade or downgrade subscription tier"""
    return subscription_controller.upgrade_subscription(upgrade_data, db, authorization)

@router.post("/subscriptions/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    cancel_data: SubscriptionCancel,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """
    Cancel subscription.
    User keeps access until end of current paid period.
    """
    return subscription_controller.cancel_subscription(cancel_data, db, authorization)

@router.post("/subscriptions/process_expiry")
async def process_subscription_expiry(
    db: Session = Depends(get_db_connection)
):
    """
    Background cron job endpoint.
    Checks and updates expired subscriptions daily.
    Should be secured or called internally only.
    """
    return subscription_controller.process_subscription_expiry(db)