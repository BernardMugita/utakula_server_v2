from typing import List, Optional, Union
import uuid
from enum import Enum
from sqlalchemy import JSON, String, Integer, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.models import Base
from utils.enums import FoodAllergy, DietaryRestriction, MedicalDietaryCondition

class MealTypeEnum(str, Enum):
    BREAKFAST = "breakfast or snack"
    SUPPER_OR_LUNCH = "lunch or supper"
    FRUIT = "fruit"
    BEVERAGE = "beverage"
    SIDE_DISH = "side dish"
    

class FoodModel(Base):
    __tablename__ = 'foods'
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4()), 
        unique=True,
        name='food_id'
    )
    image_url: Mapped[str] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    macro_nutrient: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Enum type for meal_type
    meal_type: Mapped[MealTypeEnum] = mapped_column(SqlEnum(MealTypeEnum), nullable=False)
    
    # NEW: Reference portion size (all calories are per this amount)
    reference_portion_grams: Mapped[int] = mapped_column(
        Integer,
        default=100, 
        nullable=False,
        comment="Reference portion size in grams (default 100g). All calorie data is per this amount."
    )
    
    # ARRAY columns for lists of enums - store as strings
    allergens: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=[]
    )
    dietary_tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True, 
        default=[]
    )
    suitable_for_conditions: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True, 
        default=[]
    )
    
    # Relationship with CalorieModel
    calories = relationship("CalorieModel", back_populates="food", uselist=False)