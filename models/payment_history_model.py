import uuid
from datetime import datetime
from sqlalchemy import JSON, String, Numeric, DateTime, Enum as SqlEnum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from utils.enums import PaymentMethod, PaymentStatus

class PaymentHistoryModel(Base):
    __tablename__ = 'payment_history'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()), 
        unique=True,
        name='payment_id'
    )
    
    subscription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('subscriptions.subscription_id'),
        nullable=False
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
    
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SqlEnum(PaymentMethod),
        nullable=False
    )
    
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING
    )
    
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="KES",
        nullable=False
    )
    
    payment_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="M-PESA transaction code, Stripe payment intent ID, etc."
    )
    
    payment_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="When payment was completed (null if still pending)"
    )
    
    failure_reason: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Why payment failed (if applicable)"
    )
    
    metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Provider-specific data (M-PESA response, Stripe object, etc.)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    subscription = relationship("SubscriptionModel", back_populates="payment_history")