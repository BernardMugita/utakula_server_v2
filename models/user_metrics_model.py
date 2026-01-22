import uuid
from datetime import datetime
from sqlalchemy import Boolean, Float, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base

class UserMetricsModel(Base):
    __tablename__ = 'user_metrics'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name='metrics_id'
    )
    
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Physical metrics
    gender: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="'male' or 'female'"
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    body_fat_percentage: Mapped[float] = mapped_column(
        Float, 
        nullable=False,
        comment="Body fat percentage (e.g., 20.5 for 20.5%)"
    )
    
    # Activity level for TDEE calculation
    activity_level: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        default="sedentary",
        comment="Options: sedentary, lightly_active, moderately_active, very_active, extra_active"
    )
    
    # Calculated TDEE (stored for efficiency, recalculated when metrics change)
    calculated_tdee: Mapped[float] = mapped_column(
        Float, 
        nullable=True,
        comment="Total Daily Energy Expenditure in kcal"
    )
    
    # Meta fields
    is_current: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Only one metrics entry should be current per user"
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
    
    # Relationship
    user = relationship("UserModel", back_populates="metrics")