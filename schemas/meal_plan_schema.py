import json
from typing import Dict, Union
import uuid
from pydantic import BaseModel, Field

from models.meal_plan_model import MealPlanModel

class SelectedFood(BaseModel):
    id: str | uuid.UUID
    name: str
    image_url: str
    calories: int | float
    serving_quantity: int
    
class Member(BaseModel):
    id: str

class MealPlan(BaseModel):
    """Single meal plan containing breakfast, lunch, and supper"""
    breakfast: list[SelectedFood] | list
    lunch: list[SelectedFood] | list
    supper: list[SelectedFood] | list

class DayMealPlan(BaseModel):
    """Meal plan for a single day"""
    day: str
    meal_plan: MealPlan 
    total_calories: int | float
    
class MealPlanCreate(BaseModel):
    """Schema for creating a new meal plan"""
    meal_plan: list[DayMealPlan]
    
class MealPlanPreferences(BaseModel):
    """Schema for meal plan preferences"""
    body_goal: str = Field(..., description="User's body goal, e.g., weight loss, muscle gain")
    dietary_restrictions: list[str] = Field(..., description="List of dietary restrictions, e.g., vegan, gluten-free")
    allergies: list[str] = Field(..., description="List of food allergies, e.g., nuts, dairy")
    daily_calorie_target: int = Field(..., description="Target daily calorie intake")
    medical_conditions: list[str] = Field(..., description="List of medical conditions, e.g., diabetes, hypertension")
    
class MealPlanRead(BaseModel):
    """Schema for reading a meal plan"""
    id: uuid.UUID
    user_id: str
    members: list[str | Member]
    meal_plan: list[DayMealPlan]
    
    class Config:
        from_attributes = True
    
class SuggestedMealPlan(BaseModel):
    """Schema for reading a meal plan"""
    id: str
    members: list
    meal_plan: list[DayMealPlan] | list | str
    
class MealPlanUpdate(BaseModel):
    """Schema for updating an existing meal plan"""
    meal_plan: list[DayMealPlan]
    
class SharedMealPlanRead(BaseModel):
    """Schema for reading a shared meal plan"""
    id: uuid.UUID
    user_id: str
    owner: str
    members: list[str | Member]
    meal_plan: list[DayMealPlan]
    
    class Config:
        from_attributes = True

class CreateMealPlanResponse(BaseModel):
    """Response schema for meal plan creation"""
    status: str
    message: str
    payload: MealPlanRead | str | list
    
class SuggestMealPlanResponse(BaseModel):
    """Response schema for meal plan creation"""
    status: str
    message: str
    payload: SuggestedMealPlan | str | list
    
class MealPlanGet(BaseModel):
    """Schema for getting a meal plan by ID"""
    id: uuid.UUID 
    
class RetrieveMealPlanResponse(BaseModel):
    """Response schema for retrieving meal plans"""
    status: str
    message: str
    payload: MealPlanRead | list[MealPlanRead] | str
    
class UpdateMealPlanResponse(BaseModel):
    """Response schema for meal plan updates"""
    status: str
    message: str
    payload: Union[MealPlanRead, str]
    
class FetchMemberPlansResponse(BaseModel):
    """Response schema for fetching member plans"""
    status: str
    message: str
    payload: list[SharedMealPlanRead] | str
    
    class Config:
        from_attributes = True