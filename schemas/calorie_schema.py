import uuid
from pydantic import BaseModel, Field
from typing import Optional

# Nutrient Breakdown Schema
class NutrientBreakdown(BaseModel):
    amount: float = Field(..., description="The amount of the nutrient.")
    calories: float = Field(..., description="Calories derived from the nutrient.")
    unit: str = Field(..., description="The unit for the nutrient amount, e.g., 'g'.")

class BreakdownSchema(BaseModel):
    carbohydrate: Optional[NutrientBreakdown] = None
    protein: Optional[NutrientBreakdown] = None
    fat: Optional[NutrientBreakdown] = None
    fiber: Optional[NutrientBreakdown] = None

# Calorie Data Schema
class CaloriesData(BaseModel):
    total: int
    breakdown: BreakdownSchema

# Food Creation Schema
class FoodWithCaloriesCreate(BaseModel):
    name: str
    image_url: str
    macro_nutrient: str
    meal_type: str
    dietary_tags: list[str] = []
    allergens: list[str] = []
    suitable_for_conditions: list[str] = []
    calories: CaloriesData 

class CalorieRead(BaseModel):
    calorie_id: str = Field(..., alias='id')
    food_id: str
    total: int
    breakdown: BreakdownSchema
    
    class Config:
        from_attributes = True
        populate_by_name = True

class FoodRead(BaseModel):
    food_id: uuid.UUID
    image_url: str
    name: str
    macro_nutrient: str
    meal_type: str
    calories: Optional[CalorieRead] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True

class CreateFoodResponse(BaseModel):
    status: str
    message: str
    payload: FoodRead | str

class CalorieCreate(BaseModel):
    food_id: str
    total: int
    breakdown: BreakdownSchema

class CreateCalorieResponse(BaseModel):
    status: str
    message: str
    payload: CalorieRead | str
    
class FetchCalorieResponse(BaseModel):
    status: str
    message: str
    payload: CalorieRead | list[CalorieRead] | str
    
class CalorieGet(BaseModel):
    food_id: str

class CalorieUpdate(BaseModel):
    id: uuid.UUID
    total: Optional[int] = None
    breakdown: Optional[BreakdownSchema] = None

class UpdateCalorieResponse(BaseModel):
    status: str
    message: str
    payload: CalorieRead | str