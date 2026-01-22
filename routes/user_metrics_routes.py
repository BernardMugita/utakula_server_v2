from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session
from connect import SessionLocal

from controllers.user_metrics_controller import UserMetricsController
from schemas.user_metrics_schema import (
    UserMetricsCreate, UserMetricsUpdate,
    CreateMetricsResponse, RetrieveMetricsResponse, UpdateMetricsResponse
)

router = APIRouter()
user_metrics_controller = UserMetricsController()

# Dependency to get the SQLAlchemy session
def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/metrics/create", response_model=CreateMetricsResponse)
async def create_metrics(
    metrics_data: UserMetricsCreate = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Create user metrics profile (gender, age, weight, height, body fat %, activity level)"""
    return user_metrics_controller.create_user_metrics(metrics_data, db, authorization)

@router.post("/metrics/get_current", response_model=RetrieveMetricsResponse)
async def get_current_metrics(
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get user's current metrics and calculated TDEE"""
    return user_metrics_controller.get_current_user_metrics(db, authorization)

@router.post("/metrics/update", response_model=UpdateMetricsResponse)
async def update_metrics(
    metrics_data: UserMetricsUpdate = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Update user metrics and recalculate TDEE"""
    return user_metrics_controller.update_user_metrics(metrics_data, db, authorization)