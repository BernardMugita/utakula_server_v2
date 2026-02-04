from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, JSON
import uuid
from schemas.notification_schema import NotificationFor, ScheduledJob
from models.models import Base

class NotificationModel(Base):
    __tablename__ = "notifications"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name="notification_id"
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    notifications_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    time_before_meals: Mapped[int] = mapped_column(nullable=False, default=1)
    frequency_before_meals: Mapped[int] = mapped_column(nullable=False, default=1)    
    notification_for: Mapped[list[NotificationFor]] = mapped_column(JSON, nullable=False)
    scheduled_jobs: Mapped[list[ScheduledJob]] = mapped_column(JSON, nullable=True, default=[])    
    
    user = relationship("UserModel", back_populates="notifications")