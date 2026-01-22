# schemas/user_metrics_schema.py
from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, validator

class UserMetricsCreate(BaseModel):
    """Schema for creating user metrics"""
    gender: str = Field(..., description="User's gender: 'male' or 'female'")
    age: int = Field(..., ge=10, le=120, description="User's age in years")
    weight_kg: float = Field(..., gt=0, le=500, description="User's weight in kilograms")
    height_cm: float = Field(..., gt=0, le=300, description="User's height in centimeters")
    body_fat_percentage: float = Field(..., ge=3, le=60, description="Body fat percentage (3-60%)")
    activity_level: str = Field(
        default="sedentary",
        description="Activity level: sedentary, lightly_active, moderately_active, very_active, extra_active"
    )
    
    @validator('gender')
    def validate_gender(cls, v):
        if v.lower() not in ['male', 'female']:
            raise ValueError("Gender must be 'male' or 'female'")
        return v.lower()
    
    @validator('activity_level')
    def validate_activity_level(cls, v):
        valid_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active']
        if v.lower() not in valid_levels:
            raise ValueError(f"Activity level must be one of: {', '.join(valid_levels)}")
        return v.lower()

class UserMetricsRead(BaseModel):
    """Schema for reading user metrics"""
    id: uuid.UUID
    user_id: str
    gender: str
    age: int
    weight_kg: float
    height_cm: float
    body_fat_percentage: float
    activity_level: str
    calculated_tdee: Optional[float] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserMetricsUpdate(BaseModel):
    """Schema for updating user metrics"""
    gender: Optional[str] = None
    age: Optional[int] = Field(None, ge=10, le=120)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    body_fat_percentage: Optional[float] = Field(None, ge=3, le=60)
    activity_level: Optional[str] = None
    
    @validator('gender')
    def validate_gender(cls, v):
        if v and v.lower() not in ['male', 'female']:
            raise ValueError("Gender must be 'male' or 'female'")
        return v.lower() if v else None
    
    @validator('activity_level')
    def validate_activity_level(cls, v):
        if v:
            valid_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active']
            if v.lower() not in valid_levels:
                raise ValueError(f"Activity level must be one of: {', '.join(valid_levels)}")
            return v.lower()
        return None

class CreateMetricsResponse(BaseModel):
    """Response schema for metrics creation"""
    status: str
    message: str
    payload: UserMetricsRead | str

class RetrieveMetricsResponse(BaseModel):
    """Response schema for retrieving metrics"""
    status: str
    message: str
    payload: UserMetricsRead | str

class UpdateMetricsResponse(BaseModel):
    """Response schema for metrics update"""
    status: str
    message: str
    payload: UserMetricsRead | str