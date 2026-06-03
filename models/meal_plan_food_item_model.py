from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
import uuid

class MealPlanFoodItemModel(Base):
    __tablename__ = 'meal_plan_food_item'

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        name='food_item_id'
    )

    meal_id: Mapped[str] = mapped_column(
        ForeignKey("meal_plan_meal.meal_id", ondelete="CASCADE"),
        nullable=False
    )

    # Reference only — no embedded food data
    food_id: Mapped[str] = mapped_column(
        ForeignKey("foods.food_id", ondelete="RESTRICT"), 
        nullable=False
    )

    # User-specific portion data
    grams: Mapped[float] = mapped_column(nullable=False)
    servings: Mapped[float] = mapped_column(nullable=False)

    # Relationships
    meal = relationship("MealPlanMealModel", back_populates="food_items")
    food = relationship("FoodModel")