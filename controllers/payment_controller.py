from datetime import datetime, timedelta
from fastapi import HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.payment_history_model import PaymentHistoryModel
from models.subscription_model import SubscriptionModel
from models.membership_model import MembershipModel
from schemas.payment_schema import (
    InitiatePaymentRequest, InitiatePaymentResponse,
    PaymentWebhookData, PaymentUpdate, PaymentRead, PaymentGet,
    CreatePaymentResponse, RetrievePaymentResponse, UpdatePaymentResponse
)
from utils.enums import PaymentStatus, PaymentMethod, SubscriptionStatus
from utils.helper_utils import HelperUtils

utils = HelperUtils()

class PaymentController:
    def __init__(self) -> None:
        pass
    
    def initiate_payment(self, payment_request: InitiatePaymentRequest, db: Session, authorization: str = Header(...)):
        """
        Initiate payment for subscription.
        Creates payment record and returns checkout info.
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            user_id = payload['user_id']
            
            # Get subscription
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.id == str(payment_request.subscription_id)
            ).first()
            
            if not subscription:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=InitiatePaymentResponse(
                        status="error",
                        message="Subscription not found",
                        payment_id="",
                        payment_reference=None,
                        checkout_url=None
                    ).dict()
                )
            
            # Get membership to get price
            membership = db.query(MembershipModel).filter(
                MembershipModel.id == subscription.membership_id
            ).first()
            
            # Create payment record
            new_payment = PaymentHistoryModel(
                subscription_id=str(subscription.id),
                user_id=str(subscription.user_id),
                membership_id=str(subscription.membership_id),
                payment_method=payment_request.payment_method,
                payment_status=PaymentStatus.PENDING,
                amount=membership.membership_price,
                currency="KES"
            )
            
            db.add(new_payment)
            db.commit()
            db.refresh(new_payment)
            
            # PLACEHOLDER: Initialize actual payment
            if payment_request.payment_method == PaymentMethod.MPESA:
                # TODO: Integrate Daraja API (M-PESA STK Push)
                # This will be implemented in the next 2 weeks
                payment_reference = f"MPESA-PLACEHOLDER-{new_payment.id[:8]}"
                checkout_url = None
                
                # Example of what you'll do:
                # mpesa_response = initiate_mpesa_stk_push(
                #     phone_number=payment_request.phone_number,
                #     amount=membership.membership_price,
                #     account_reference=f"UTAKULA-{subscription.id[:8]}"
                # )
                # payment_reference = mpesa_response['CheckoutRequestID']
                
            elif payment_request.payment_method == PaymentMethod.STRIPE:
                # TODO: Integrate Stripe Checkout
                # This will be implemented in the next 2 weeks
                payment_reference = f"STRIPE-PLACEHOLDER-{new_payment.id[:8]}"
                checkout_url = f"https://checkout.stripe.com/placeholder/{new_payment.id}"
                
                # Example of what you'll do:
                # stripe_session = stripe.checkout.Session.create(
                #     payment_method_types=['card'],
                #     line_items=[{
                #         'price_data': {
                #             'currency': 'kes',
                #             'product_data': {'name': membership.membership_name},
                #             'unit_amount': int(membership.membership_price * 100),
                #         },
                #         'quantity': 1,
                #     }],
                #     mode='payment',
                #     success_url='YOUR_SUCCESS_URL',
                #     cancel_url='YOUR_CANCEL_URL',
                # )
                # payment_reference = stripe_session.id
                # checkout_url = stripe_session.url
                
            else:
                payment_reference = f"OTHER-{new_payment.id[:8]}"
                checkout_url = None
            
            # Update payment with reference
            new_payment.payment_reference = payment_reference
            db.commit()
            
            return InitiatePaymentResponse(
                status="success",
                message="Payment initiated successfully",
                payment_id=str(new_payment.id),
                payment_reference=payment_reference,
                checkout_url=checkout_url
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=InitiatePaymentResponse(
                    status="error",
                    message=f"Error initiating payment: {str(e)}",
                    payment_id="",
                    payment_reference=None,
                    checkout_url=None
                ).dict()
            )
    
    def handle_payment_webhook(self, webhook_data: PaymentWebhookData, db: Session):
        """
        Handle payment confirmation webhook from M-PESA or Stripe.
        This is called by the payment provider when payment succeeds/fails.
        """
        try:
            # Find payment by reference
            payment = db.query(PaymentHistoryModel).filter(
                PaymentHistoryModel.payment_reference == webhook_data.payment_reference
            ).first()
            
            if not payment:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={
                        "status": "error",
                        "message": "Payment not found"
                    }
                )
            
            # Update payment status
            payment.payment_status = webhook_data.status
            payment.payment_date = datetime.utcnow() if webhook_data.status == PaymentStatus.COMPLETED else None
            payment.metadata = webhook_data.metadata
            
            # If payment successful, update subscription
            if webhook_data.status == PaymentStatus.COMPLETED:
                subscription = db.query(SubscriptionModel).filter(
                    SubscriptionModel.id == payment.subscription_id
                ).first()
                
                if subscription:
                    # Calculate new subscription dates
                    now = datetime.utcnow()
                    
                    # If in grace period, start from grace period end
                    if subscription.subscription_status == SubscriptionStatus.GRACE_PERIOD:
                        start_date = subscription.grace_period_end_date
                    else:
                        start_date = now
                    
                    end_date = start_date + timedelta(days=30)  # 30-day subscription
                    
                    # Update subscription
                    subscription.subscription_status = SubscriptionStatus.ACTIVE
                    subscription.subscription_start_date = start_date
                    subscription.subscription_end_date = end_date
                    subscription.next_billing_date = end_date
                    subscription.payment_method = webhook_data.payment_method
                    subscription.payment_reference = webhook_data.payment_reference
                    subscription.amount_paid = webhook_data.amount
                    subscription.grace_periods_used = 0  # Reset grace period count
                    subscription.grace_period_start_date = None
                    subscription.grace_period_end_date = None
            
            db.commit()
            
            return {
                "status": "success",
                "message": "Payment processed successfully"
            }
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": f"Error processing webhook: {str(e)}"
                }
            )
    
    def get_user_payment_history(self, user_id: str, db: Session, authorization: str = Header(...)):
        """Get all payment history for a user"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            payments = db.query(PaymentHistoryModel).filter(
                PaymentHistoryModel.user_id == user_id
            ).order_by(PaymentHistoryModel.created_at.desc()).all()
            
            payment_list = [PaymentRead.from_orm(p) for p in payments]
            
            return RetrievePaymentResponse(
                status="success",
                message="User payment history",
                payload=payment_list
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrievePaymentResponse(
                    status="error",
                    message="Error retrieving payment history",
                    payload=str(e)
                ).dict()
            )
    
    def get_payment_by_id(self, payment_data: PaymentGet, db: Session, authorization: str = Header(...)):
        """Get specific payment details"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            payment = db.query(PaymentHistoryModel).filter(
                PaymentHistoryModel.id == str(payment_data.payment_id)
            ).first()
            
            if not payment:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrievePaymentResponse(
                        status="error",
                        message="Payment not found",
                        payload="The requested payment does not exist"
                    ).dict()
                )
            
            return RetrievePaymentResponse(
                status="success",
                message="Payment details",
                payload=PaymentRead.from_orm(payment)
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrievePaymentResponse(
                    status="error",
                    message="Error retrieving payment",
                    payload=str(e)
                ).dict()
            )