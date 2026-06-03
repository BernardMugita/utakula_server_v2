from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from models.meal_plan_food_item_model import MealPlanFoodItemModel
import uuid

class MealPlanMealModel(Base):
    __tablename__ = 'meal_plan_meal'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name='meal_id'
    )

    day_plan_id: Mapped[str] = mapped_column(
        ForeignKey("meal_plan_day.day_id", ondelete="CASCADE"),
        nullable=False
    )

    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "breakfast", "lunch", "supper"

    # Relationships
    food_items = relationship("MealPlanFoodItemModel", back_populates="meal", cascade="all, delete-orphan")
    day_plan = relationship("MealPlanDayModel", back_populates="meals")