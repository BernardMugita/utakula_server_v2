# schemas/meal_plan_schema.py
from typing import Dict, Optional, Union
import uuid
from pydantic import BaseModel, Field


class MacroBreakdown(BaseModel):
    """Macro nutrient breakdown for a food portion"""
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


class SelectedFood(BaseModel):
    """Food item as returned by _hydrate_meal_plan"""
    id: str
    name: str
    image_url: str
    grams: float
    servings: float
    calories_per_100g: float
    total_calories: float
    macros: Optional[MacroBreakdown] = None


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
    total_macros: Optional[MacroBreakdown] = None


# ── Input schemas (what the app sends up) ────────────────────────────────────

class MealPlanCreate(BaseModel):
    """Schema for creating a new meal plan"""
    meal_plan: list[DayMealPlan]


class MealPlanUpdate(BaseModel):
    """Schema for updating an existing meal plan"""
    meal_plan: list[DayMealPlan]


class MealPlanPreferences(BaseModel):
    """Schema for meal plan preferences with optional TDEE override"""
    body_goal: str = Field(..., description="User's body goal: WEIGHT_LOSS, MUSCLE_GAIN, or MAINTENANCE")
    dietary_restrictions: Optional[list[str]] = Field(default=[], description="List of dietary restrictions")
    allergies: Optional[list[str]] = Field(default=[], description="List of food allergies")
    medical_conditions: Optional[list[str]] = Field(default=[], description="List of medical conditions")
    daily_calorie_target: Optional[int] = Field(None, description="Optional manual calorie target override.")
    use_calculated_tdee: bool = Field(default=True, description="If True, uses TDEE from user metrics.")


# ── Read schemas (what the API sends back) ───────────────────────────────────

class MealPlanRead(BaseModel):
    """Schema for reading a meal plan — matches _hydrate_meal_plan output"""
    id: str
    user_id: str
    members: list
    meal_plan: list[DayMealPlan]

    class Config:
        from_attributes = True


class SharedMealPlanRead(BaseModel):
    """Schema for reading a shared meal plan"""
    id: str
    user_id: str
    owner: str
    members: list
    meal_plan: list[DayMealPlan]

    class Config:
        from_attributes = True


class SuggestedMealPlan(BaseModel):
    """Schema for a suggested meal plan (not yet saved)"""
    id: str
    members: list
    meal_plan: list[DayMealPlan] | list | str
    calculated_tdee: Optional[float] = None
    target_calories: Optional[float] = None


class MealPlanGet(BaseModel):
    """Schema for getting a meal plan by ID"""
    id: uuid.UUID


# ── Response schemas ──────────────────────────────────────────────────────────

class CreateMealPlanResponse(BaseModel):
    status: str
    message: str
    payload: MealPlanRead | str | list


class SuggestMealPlanResponse(BaseModel):
    status: str
    message: str
    payload: SuggestedMealPlan | str | list


class RetrieveMealPlanResponse(BaseModel):
    status: str
    message: str
    payload: MealPlanRead | list[MealPlanRead] | str


class UpdateMealPlanResponse(BaseModel):
    status: str
    message: str
    payload: MealPlanRead | str


class FetchMemberPlansResponse(BaseModel):
    status: str
    message: str
    payload: list[SharedMealPlanRead] | str

    class Config:
        from_attributes = True