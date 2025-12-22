
from datetime import time
from pydantic import BaseModel, field_validator
from enum import Enum

class MealEnum(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "supper"

class NotificationFor(BaseModel):
    meal: MealEnum
    meal_time: time
    
    @field_validator('meal_time', mode='before')
    @classmethod
    def parse_time(cls, v):
        if isinstance(v, str):
            # Handle "0800" format
            if len(v) == 4 and v.isdigit():
                hour = int(v[:2])
                minute = int(v[2:])
                return time(hour=hour, minute=minute)
            # Handle "08:00" format
            elif ':' in v:
                parts = v.split(':')
                return time(hour=int(parts[0]), minute=int(parts[1]))
        return v
    
class NotificationSettings(BaseModel):
    time_before_meals: int
    frequency_before_meals: int
    notification_for: list[NotificationFor]
    
class NotificationFoods(BaseModel):
    name: str
    image_url: str
    
class MealPlanNotification(BaseModel):
    notification_time: str
    notification_title: str
    notification_message: str
    food_images: list = []
    
class NotificationHandlerResponse(BaseModel):
    status: str
    message: str
    payload: str | MealPlanNotification | None = None
