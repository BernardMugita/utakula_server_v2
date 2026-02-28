import uuid
from datetime import datetime
from sqlalchemy import JSON, String, Boolean, Numeric, DateTime, Enum as SqlEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from utils.enums import MembershipType, BillingCycle

class MembershipModel(Base):
    __tablename__ = 'memberships'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()), 
        unique=True,
        name='membership_id'
    )
    
    membership_type: Mapped[MembershipType] = mapped_column(
        SqlEnum(MembershipType), 
        nullable=False,
        unique=True
    )
    
    membership_name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Display name: 'Utakula Plus', 'Utakula Elite'"
    )
    
    membership_description: Mapped[str] = mapped_column(
        Text, 
        nullable=True
    )
    
    membership_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False,
        comment="Price in KES"
    )
    
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        SqlEnum(BillingCycle), 
        nullable=False,
        default=BillingCycle.MONTHLY,
        comment="Not used yet, but available for future quarterly/annual plans"
    )
    
    features: Mapped[dict] = mapped_column(
        JSON, 
        nullable=True,
        default=dict,
        comment="JSON list of features included in this membership"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        nullable=False,
        comment="Can this plan be purchased?"
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
    
    # Relationship to subscriptions
    subscriptions = relationship("SubscriptionModel", back_populates="membership")