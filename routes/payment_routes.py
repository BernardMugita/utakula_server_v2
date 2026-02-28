from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session
from connect import SessionLocal

from controllers.payment_controller import PaymentController
from schemas.payment_schema import (
    InitiatePaymentRequest, InitiatePaymentResponse,
    PaymentWebhookData, PaymentGet,
    RetrievePaymentResponse
)

router = APIRouter()
payment_controller = PaymentController()

def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/payments/initiate", response_model=InitiatePaymentResponse)
async def initiate_payment(
    payment_request: InitiatePaymentRequest,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """
    Initiate payment for subscription.
    Returns checkout URL (Stripe) or payment reference (M-PESA).
    """
    return payment_controller.initiate_payment(payment_request, db, authorization)

@router.post("/payments/webhook/mpesa")
async def mpesa_webhook(
    webhook_data: PaymentWebhookData,
    db: Session = Depends(get_db_connection)
):
    """
    M-PESA payment confirmation webhook.
    Called by Safaricom when payment is processed.
    
    TODO: Add Daraja API signature verification for security.
    """
    return payment_controller.handle_payment_webhook(webhook_data, db)

@router.post("/payments/webhook/stripe")
async def stripe_webhook(
    webhook_data: PaymentWebhookData,
    db: Session = Depends(get_db_connection)
):
    """
    Stripe payment confirmation webhook.
    Called by Stripe when payment is processed.
    
    TODO: Add Stripe signature verification for security.
    """
    return payment_controller.handle_payment_webhook(webhook_data, db)

@router.post("/payments/history/{user_id}", response_model=RetrievePaymentResponse)
async def get_payment_history(
    user_id: str,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get all payment history for a user"""
    return payment_controller.get_user_payment_history(user_id, db, authorization)

@router.post("/payments/get_by_id", response_model=RetrievePaymentResponse)
async def get_payment(
    payment_data: PaymentGet = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get specific payment details"""
    return payment_controller.get_payment_by_id(payment_data, db, authorization)