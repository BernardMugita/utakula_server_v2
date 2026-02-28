import uuid
from typing import Optional, Dict, Union, List
from datetime import datetime
from pydantic import BaseModel
from utils.enums import PaymentMethod, PaymentStatus

class PaymentCreate(BaseModel):
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    payment_method: PaymentMethod
    amount: float
    currency: str = "KES"
    payment_reference: Optional[str] = None
    metadata: Optional[Dict] = {}

class PaymentUpdate(BaseModel):
    payment_id: uuid.UUID
    payment_status: PaymentStatus
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Optional[Dict] = None

class PaymentRead(BaseModel):
    payment_id: uuid.UUID
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    amount: float
    currency: str
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Optional[Dict] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentGet(BaseModel):
    payment_id: uuid.UUID

class InitiatePaymentRequest(BaseModel):
    subscription_id: uuid.UUID
    payment_method: PaymentMethod
    phone_number: Optional[str] = None  # For M-PESA

class InitiatePaymentResponse(BaseModel):
    status: str
    message: str
    payment_id: str
    payment_reference: Optional[str] = None
    checkout_url: Optional[str] = None  # For Stripe

class PaymentWebhookData(BaseModel):
    payment_reference: str
    payment_method: PaymentMethod
    amount: float
    currency: str = "KES"
    status: PaymentStatus
    metadata: Optional[Dict] = {}

class CreatePaymentResponse(BaseModel):
    status: str
    message: str
    payload: Union[PaymentRead, str]

class RetrievePaymentResponse(BaseModel):
    status: str
    message: str
    payload: Union[PaymentRead, List[PaymentRead], str]

class UpdatePaymentResponse(BaseModel):
    status: str
    message: str
    payload: Union[PaymentRead, str]