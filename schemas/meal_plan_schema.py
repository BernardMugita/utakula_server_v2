# schemas/meal_plan_schema.py
import json
from typing import Dict, Optional, Union
import uuid
from pydantic import BaseModel, Field

from models.meal_plan_model import MealPlanModel

class MacroBreakdown(BaseModel):
    """Macro nutrient breakdown for a food portion"""
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float

class SelectedFood(BaseModel):
    """
    Updated food selection with grams-based approach
    """
    id: str | uuid.UUID
    name: str
    image_url: str
    
    # NEW: Grams and servings
    grams: float = Field(..., description="Actual weight in grams for this portion")
    servings: float = Field(..., description="Number of servings (for display, based on 100g reference)")
    
    # Calorie information
    calories_per_100g: float = Field(..., description="Base calories per 100g")
    total_calories: float = Field(..., description="Total calories for this portion")
    
    # Optional: Macro breakdown for this specific portion
    macros: Optional[MacroBreakdown] = Field(None, description="Macronutrient breakdown for this portion")

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
    total_calories: float
    total_macros: Optional[MacroBreakdown] = None  # NEW: Daily macro totals
    
class MealPlanCreate(BaseModel):
    """Schema for creating a new meal plan"""
    meal_plan: list[DayMealPlan]
    
class MealPlanPreferences(BaseModel):
    """Schema for meal plan preferences with optional TDEE override"""
    body_goal: str = Field(..., description="User's body goal: WEIGHT_LOSS, MUSCLE_GAIN, or MAINTENANCE")
    dietary_restrictions: Optional[list[str]] = Field(default=[], description="List of dietary restrictions")
    allergies: Optional[list[str]] = Field(default=[], description="List of food allergies")
    medical_conditions: Optional[list[str]] = Field(default=[], description="List of medical conditions")
    
    # NEW: Optional override for manual calorie target
    daily_calorie_target: Optional[int] = Field(
        None, 
        description="Optional: Manual calorie target override. If not provided, calculates from user metrics."
    )
    use_calculated_tdee: bool = Field(
        default=True,
        description="If True, uses TDEE from user metrics. If False, requires daily_calorie_target."
    )
    
class MealPlanRead(BaseModel):
    """Schema for reading a meal plan"""
    id: uuid.UUID
    user_id: str
    members: list[str | Member]
    meal_plan: list[DayMealPlan]
    
    class Config:
        from_attributes = True
    
class SuggestedMealPlan(BaseModel):
    """Schema for reading a suggested meal plan"""
    id: str
    members: list
    meal_plan: list[DayMealPlan] | list | str
    calculated_tdee: Optional[float] = None  # NEW: Include TDEE used
    target_calories: Optional[float] = None  # NEW: Target after goal adjustment
    
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
    """Response schema for meal plan suggestion"""
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