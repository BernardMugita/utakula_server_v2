from datetime import time
from pydantic import BaseModel, field_validator, field_serializer
from enum import Enum
from typing import Union

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
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            # Handle "0800" format
            if len(v) == 4 and v.isdigit():
                hour = int(v[:2])
                minute = int(v[2:])
                return time(hour=hour, minute=minute)
            # Handle "08:00" or "08:00:00" format
            elif ':' in v:
                parts = v.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                second = int(parts[2]) if len(parts) > 2 else 0
                return time(hour=hour, minute=minute, second=second)
        raise ValueError(f"Invalid time format: {v}")
    
    @field_serializer('meal_time')
    def serialize_time(self, meal_time: time, _info):
        # Serialize time to "HH:MM" format
        return meal_time.strftime("%H:%M")

class NotificationSettings(BaseModel):
    notifications_enabled: bool = True
    time_before_meals: int | float
    frequency_before_meals: int
    notification_for: list[NotificationFor]
    
class NotificationsTestSchema(BaseModel):
    user_id: str
    
# Add to notification_schema.py

class SendNotificationRequest(BaseModel):
    meal: MealEnum  # breakfast, lunch, or supper
    
class ScheduledJob(BaseModel):
    id: str
    next_run_time: Union[str, None]
    func_name: str
    trigger: str
    
class NotificationFoods(BaseModel):
    name: str
    image_url: str
    
class MealPlanNotification(BaseModel):
    notification_time: str
    notification_title: str
    notification_message: str
    food_images: list = []
    
class NotificationBody(BaseModel):
    title: str
    body: str
    food_images: list[str]
    
class NotificationHandlerResponse(BaseModel):
    status: str
    message: str
    payload: Union[str, MealPlanNotification, NotificationSettings, NotificationBody, None, list] = None