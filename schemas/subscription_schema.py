import uuid
from typing import Optional, Union, List
from datetime import datetime
from pydantic import BaseModel
from utils.enums import SubscriptionStatus, PaymentMethod

class SubscriptionCreate(BaseModel):
    user_id: uuid.UUID
    membership_id: uuid.UUID
    
class SubscriptionUpgrade(BaseModel):
    subscription_id: uuid.UUID
    new_membership_id: uuid.UUID

class SubscriptionCancel(BaseModel):
    subscription_id: uuid.UUID
    cancellation_reason: Optional[str] = None

class SubscriptionRead(BaseModel):
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    subscription_status: SubscriptionStatus
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    amount_paid: Optional[float] = None
    currency: str
    subscription_start_date: datetime
    subscription_end_date: datetime
    next_billing_date: Optional[datetime] = None
    auto_renew: bool
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    trial_used: bool
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    grace_period_start_date: Optional[datetime] = None
    grace_period_end_date: Optional[datetime] = None
    grace_periods_used: int
    days_remaining: Optional[int] = None  # Computed field
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionStatusCheck(BaseModel):
    user_id: uuid.UUID

class SubscriptionStatusResponse(BaseModel):
    has_active_subscription: bool
    subscription_status: Optional[SubscriptionStatus] = None
    days_remaining: Optional[int] = None
    features_available: bool
    message: str

class CreateSubscriptionResponse(BaseModel):
    status: str
    message: str
    payload: Union[SubscriptionRead, str]

class RetrieveSubscriptionResponse(BaseModel):
    status: str
    message: str
    payload: Union[SubscriptionRead, List[SubscriptionRead], str]

class UpdateSubscriptionResponse(BaseModel):
    status: str
    message: str
    payload: Union[SubscriptionRead, str]

class CancelSubscriptionResponse(BaseModel):
    status: str
    message: str
    payload: Union[SubscriptionRead, str]