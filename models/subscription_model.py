import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Numeric, DateTime, Enum as SqlEnum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from utils.enums import SubscriptionStatus, PaymentMethod

class SubscriptionModel(Base):
    __tablename__ = 'subscriptions'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()), 
        unique=True,
        name='subscription_id'
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.user_id'),
        nullable=False
    )
    
    membership_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('memberships.membership_id'),
        nullable=False
    )
    
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SqlEnum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.TRIAL
    )
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SqlEnum(PaymentMethod),
        nullable=True,
        comment="Payment method used for this subscription"
    )
    
    payment_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="M-PESA code, Stripe payment intent, etc."
    )
    
    amount_paid: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Amount paid for current period"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="KES",
        nullable=False
    )
    
    subscription_start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When current subscription period started"
    )
    
    subscription_end_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="When current subscription period ends"
    )
    
    next_billing_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Next date to attempt payment (if auto-renew enabled)"
    )
    
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Should subscription auto-renew?"
    )
    
    cancelled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    
    cancellation_reason: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    # Free Trial Fields
    trial_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has user ever used their free trial?"
    )
    
    trial_start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    
    trial_end_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # Grace Period Fields
    grace_period_start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="When grace period started"
    )
    
    grace_period_end_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="When grace period ends (7 days from start)"
    )
    
    grace_periods_used: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="How many grace periods used (resets on successful payment)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    membership = relationship("MembershipModel", back_populates="subscriptions")
    payment_history = relationship("PaymentHistoryModel", back_populates="subscription")