from typing import List, Optional, Union
import uuid
from pydantic import BaseModel

from schemas.calorie_schema import CalorieRead


class FoodCreate(BaseModel):
    image_url: str
    name: str
    macro_nutrient: str
    meal_type: str
    dietary_tags: List[str] = []
    allergens: List[str] = []
    suitable_for_conditions: List[str] = []
    calories: CalorieRead
    
class FoodRead(BaseModel):
    food_id: uuid.UUID
    name: str
    calories: Optional[CalorieRead] = None
    image_url: str
    macro_nutrient: str
    meal_type: str
    reference_portion_grams: int
    dietary_tags: List[str] = []
    allergens: List[str] = []
    suitable_for_conditions: List[str] = []

class CreateFoodResponse(BaseModel):
    status: str
    message: str
    payload: Union[List[FoodRead], FoodRead, str, List]
    
class CreateBulkFoodResponse(BaseModel):
    status: str
    message: str
    payload: List[FoodRead] | str

class FoodUpdate(BaseModel):
    id: uuid.UUID
    image_url: str
    name: str
    macro_nutrient: str
    meal_type: str

class FoodGet(BaseModel):
    id: uuid.UUID    
    
class FoodDelete(BaseModel):
    id: uuid.UUID
    
class RetrieveFoodResponse(BaseModel):
    status: str
    message: str
    payload: FoodRead | list[FoodRead] | str
    
class UpdateFoodResponse(BaseModel):
    status: str
    message: str
    payload: FoodRead | str
    
class DeleteFoodResponse(BaseModel):
    status: str
    payload: str
    
    class Config:
        from_attributes = True