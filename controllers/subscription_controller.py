from datetime import datetime, timedelta
from fastapi import HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.subscription_model import SubscriptionModel
from models.membership_model import MembershipModel
from schemas.subscription_schema import (
    SubscriptionCreate, SubscriptionRead, SubscriptionUpgrade, SubscriptionCancel,
    SubscriptionStatusCheck, SubscriptionStatusResponse,
    CreateSubscriptionResponse, RetrieveSubscriptionResponse, UpdateSubscriptionResponse, CancelSubscriptionResponse
)
from utils.enums import SubscriptionStatus
from utils.helper_utils import HelperUtils

utils = HelperUtils()

class SubscriptionController:
    def __init__(self) -> None:
        pass
    
    def start_trial(self, subscription_data: SubscriptionCreate, db: Session, authorization: str = Header(...)):
        """
        Start free trial for user on signup.
        This is called automatically when user creates account.
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            # Check if user already has a subscription
            existing_subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == str(subscription_data.user_id)
            ).first()
            
            if existing_subscription:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=CreateSubscriptionResponse(
                        status="error",
                        message="User already has a subscription",
                        payload="Cannot start trial, subscription exists"
                    ).dict()
                )
            
            # Verify membership exists
            membership = db.query(MembershipModel).filter(
                MembershipModel.id == str(subscription_data.membership_id)
            ).first()
            
            if not membership:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=CreateSubscriptionResponse(
                        status="error",
                        message="Membership not found",
                        payload="The selected membership does not exist"
                    ).dict()
                )
            
            # Calculate trial dates
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=14)
            
            # Create subscription with trial
            new_subscription = SubscriptionModel(
                user_id=str(subscription_data.user_id),
                membership_id=str(subscription_data.membership_id),
                subscription_status=SubscriptionStatus.TRIAL,
                trial_used=True,
                trial_start_date=trial_start,
                trial_end_date=trial_end,
                subscription_start_date=trial_start,
                subscription_end_date=trial_end,
                auto_renew=True,
                currency="KES"
            )
            
            db.add(new_subscription)
            db.commit()
            db.refresh(new_subscription)
            
            # Add days_remaining for response
            subscription_read = SubscriptionRead.from_orm(new_subscription)
            subscription_read.days_remaining = 14
            
            return CreateSubscriptionResponse(
                status="success",
                message="Free trial started! You have 14 days of full access.",
                payload=subscription_read
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateSubscriptionResponse(
                    status="error",
                    message="Error starting trial",
                    payload=str(e)
                ).dict()
            )
    
    def check_subscription_status(self, user_data: SubscriptionStatusCheck, db: Session, authorization: str = Header(...)):
        """
        Check user's current subscription status and feature access.
        This is called on app launch and when accessing premium features.
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == str(user_data.user_id)
            ).first()
            
            if not subscription:
                return SubscriptionStatusResponse(
                    has_active_subscription=False,
                    subscription_status=None,
                    days_remaining=None,
                    features_available=False,
                    message="No subscription found. Please start your free trial."
                )
            
            now = datetime.utcnow()
            days_remaining = (subscription.subscription_end_date - now).days
            
            # Determine feature access based on status
            features_available = False
            message = ""
            
            if subscription.subscription_status == SubscriptionStatus.TRIAL:
                features_available = True
                message = f"Trial active. {days_remaining} days remaining."
            
            elif subscription.subscription_status == SubscriptionStatus.ACTIVE:
                features_available = True
                message = f"Subscription active. {days_remaining} days remaining."
            
            elif subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
                features_available = True
                message = f"Grace period active. Please update payment. {days_remaining} days remaining."
            
            elif subscription.subscription_status == SubscriptionStatus.EXPIRED:
                features_available = False
                message = "Subscription expired. Renew to restore access."
            
            elif subscription.subscription_status == SubscriptionStatus.CANCELLED:
                # Check if still within paid period
                if now <= subscription.subscription_end_date:
                    features_available = True
                    message = f"Subscription cancelled but active until {subscription.subscription_end_date.strftime('%Y-%m-%d')}."
                else:
                    features_available = False
                    message = "Subscription ended. Renew to restore access."
            
            return SubscriptionStatusResponse(
                has_active_subscription=True,
                subscription_status=subscription.subscription_status,
                days_remaining=days_remaining if days_remaining > 0 else 0,
                features_available=features_available,
                message=message
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "has_active_subscription": False,
                    "subscription_status": None,
                    "days_remaining": None,
                    "features_available": False,
                    "message": f"Error checking subscription: {str(e)}"
                }
            )
    
    def get_user_subscription(self, user_data: SubscriptionStatusCheck, db: Session, authorization: str = Header(...)):
        """Get detailed subscription info for a user"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == str(user_data.user_id)
            ).first()
            
            if not subscription:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrieveSubscriptionResponse(
                        status="error",
                        message="No subscription found",
                        payload="User does not have a subscription"
                    ).dict()
                )
            
            # Calculate days remaining
            now = datetime.utcnow()
            days_remaining = (subscription.subscription_end_date - now).days
            
            subscription_read = SubscriptionRead.from_orm(subscription)
            subscription_read.days_remaining = days_remaining if days_remaining > 0 else 0
            
            return RetrieveSubscriptionResponse(
                status="success",
                message="User subscription details",
                payload=subscription_read
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveSubscriptionResponse(
                    status="error",
                    message="Error retrieving subscription",
                    payload=str(e)
                ).dict()
            )
    
    def upgrade_subscription(self, upgrade_data: SubscriptionUpgrade, db: Session, authorization: str = Header(...)):
        """Upgrade from PLUS to ELITE (or downgrade)"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.id == str(upgrade_data.subscription_id)
            ).first()
            
            if not subscription:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=UpdateSubscriptionResponse(
                        status="error",
                        message="Subscription not found",
                        payload="The subscription does not exist"
                    ).dict()
                )
            
            # Verify new membership exists
            new_membership = db.query(MembershipModel).filter(
                MembershipModel.id == str(upgrade_data.new_membership_id)
            ).first()
            
            if not new_membership:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=UpdateSubscriptionResponse(
                        status="error",
                        message="Membership not found",
                        payload="The selected membership does not exist"
                    ).dict()
                )
            
            # Update membership
            subscription.membership_id = str(upgrade_data.new_membership_id)
            
            db.commit()
            db.refresh(subscription)
            
            # Calculate days remaining
            now = datetime.utcnow()
            days_remaining = (subscription.subscription_end_date - now).days
            
            subscription_read = SubscriptionRead.from_orm(subscription)
            subscription_read.days_remaining = days_remaining if days_remaining > 0 else 0
            
            return UpdateSubscriptionResponse(
                status="success",
                message="Subscription updated successfully",
                payload=subscription_read
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=UpdateSubscriptionResponse(
                    status="error",
                    message="Error upgrading subscription",
                    payload=str(e)
                ).dict()
            )
    
    def cancel_subscription(self, cancel_data: SubscriptionCancel, db: Session, authorization: str = Header(...)):
        """
        Cancel subscription.
        User keeps access until end of paid period.
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.id == str(cancel_data.subscription_id)
            ).first()
            
            if not subscription:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=CancelSubscriptionResponse(
                        status="error",
                        message="Subscription not found",
                        payload="The subscription does not exist"
                    ).dict()
                )
            
            # Update subscription
            subscription.subscription_status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.cancellation_reason = cancel_data.cancellation_reason
            subscription.auto_renew = False
            
            db.commit()
            db.refresh(subscription)
            
            # Calculate days remaining
            now = datetime.utcnow()
            days_remaining = (subscription.subscription_end_date - now).days
            
            subscription_read = SubscriptionRead.from_orm(subscription)
            subscription_read.days_remaining = days_remaining if days_remaining > 0 else 0
            
            return CancelSubscriptionResponse(
                status="success",
                message=f"Subscription cancelled. You will retain access until {subscription.subscription_end_date.strftime('%Y-%m-%d')}.",
                payload=subscription_read
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CancelSubscriptionResponse(
                    status="error",
                    message="Error cancelling subscription",
                    payload=str(e)
                ).dict()
            )
    
    def process_subscription_expiry(self, db: Session):
        """
        Background job to check and update expired subscriptions.
        Run this daily via cron job.
        """
        try:
            now = datetime.utcnow()
            
            # Find subscriptions that have expired
            expired_subscriptions = db.query(SubscriptionModel).filter(
                SubscriptionModel.subscription_end_date <= now,
                SubscriptionModel.subscription_status.in_([
                    SubscriptionStatus.TRIAL,
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.GRACE_PERIOD
                ])
            ).all()
            
            for subscription in expired_subscriptions:
                if subscription.subscription_status == SubscriptionStatus.TRIAL:
                    # Trial expired, start first grace period
                    subscription.subscription_status = SubscriptionStatus.GRACE_PERIOD
                    subscription.grace_period_start_date = now
                    subscription.grace_period_end_date = now + timedelta(days=7)
                    subscription.subscription_end_date = subscription.grace_period_end_date
                    subscription.grace_periods_used = 1
                
                elif subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
                    if subscription.grace_periods_used < 2:
                        # Start second grace period
                        subscription.grace_period_start_date = now
                        subscription.grace_period_end_date = now + timedelta(days=7)
                        subscription.subscription_end_date = subscription.grace_period_end_date
                        subscription.grace_periods_used = 2
                    else:
                        # Hard cutoff after second grace period
                        subscription.subscription_status = SubscriptionStatus.EXPIRED
                
                elif subscription.subscription_status == SubscriptionStatus.ACTIVE:
                    # Paid subscription expired, check if auto-renew
                    if subscription.auto_renew:
                        # Start grace period (payment failed or needs processing)
                        subscription.subscription_status = SubscriptionStatus.GRACE_PERIOD
                        subscription.grace_period_start_date = now
                        subscription.grace_period_end_date = now + timedelta(days=7)
                        subscription.subscription_end_date = subscription.grace_period_end_date
                        subscription.grace_periods_used = 1
                    else:
                        # No auto-renew, expire immediately
                        subscription.subscription_status = SubscriptionStatus.EXPIRED
            
            db.commit()
            
            return {
                "status": "success",
                "message": f"Processed {len(expired_subscriptions)} expired subscriptions"
            }
            
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"Error processing expirations: {str(e)}"
            }