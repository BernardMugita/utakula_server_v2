from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from models.meal_plan_day_model import MealPlanDayModel
import uuid

class MealPlanModel(Base):
    __tablename__ = 'meal_plan'

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()),  
        unique=True,
        name='meal_plan_id'
    )
    
    # Use UUID for the user_id field to match UserModel's ID type
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    
    members: Mapped[list] = mapped_column(JSON, nullable=False)
    
    meal_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    day_plans = relationship("MealPlanDayModel", back_populates="meal_plan", cascade="all, delete-orphan")

    # Define the reverse relationship with UserModel
    user = relationship("UserModel", back_populates="meal_plan")
