from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from models.meal_plan_meal_model import MealPlanMealModel
import uuid

class MealPlanDayModel(Base):
    __tablename__ = 'meal_plan_day'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name='day_id'
    )

    meal_plan_id: Mapped[str] = mapped_column(
        ForeignKey("meal_plan.meal_plan_id", ondelete="CASCADE"),
        nullable=False
    )

    day: Mapped[str] = mapped_column(String(20), nullable=False)  # "Monday", "Tuesday" etc.
    total_calories: Mapped[float] = mapped_column(nullable=False, default=0.0)

    # Relationships
    meals = relationship("MealPlanMealModel", back_populates="day_plan", cascade="all, delete-orphan")
    meal_plan = relationship("MealPlanModel", back_populates="day_plans")