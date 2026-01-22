# controllers/user_metrics_controller.py
import logging
from fastapi import HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.user_metrics_model import UserMetricsModel
from schemas.user_metrics_schema import (
    UserMetricsCreate, UserMetricsRead, UserMetricsUpdate,
    CreateMetricsResponse, RetrieveMetricsResponse, UpdateMetricsResponse
)
from controllers.helpers.tdee_calculator import TDEECalculator
from utils.helper_utils import HelperUtils

utils = HelperUtils()
logger = logging.getLogger(__name__)

class UserMetricsController:
    def __init__(self) -> None:
        pass
    
    def create_user_metrics(
        self, 
        metrics_data: UserMetricsCreate, 
        db: Session, 
        authorization: str = Header(...)
    ):
        """
        Create user metrics and calculate TDEE
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            user_id = payload['user_id']
            
            # Check if user already has current metrics
            existing_metrics = db.query(UserMetricsModel).filter(
                UserMetricsModel.user_id == user_id,
                UserMetricsModel.is_current == True
            ).first()
            
            if existing_metrics:
                # Set existing as not current
                existing_metrics.is_current = False
            
            # Calculate TDEE
            tdee = TDEECalculator.calculate_tdee(
                weight_kg=metrics_data.weight_kg,
                body_fat_percentage=metrics_data.body_fat_percentage,
                activity_level=metrics_data.activity_level
            )
            
            # Create new metrics
            new_metrics = UserMetricsModel(
                user_id=user_id,
                gender=metrics_data.gender,
                age=metrics_data.age,
                weight_kg=metrics_data.weight_kg,
                height_cm=metrics_data.height_cm,
                body_fat_percentage=metrics_data.body_fat_percentage,
                activity_level=metrics_data.activity_level,
                calculated_tdee=tdee,
                is_current=True
            )
            
            db.add(new_metrics)
            db.commit()
            db.refresh(new_metrics)
            
            return CreateMetricsResponse(
                status="success",
                message=f"User metrics created successfully. Calculated TDEE: {tdee:.0f} kcal/day",
                payload=UserMetricsRead.from_orm(new_metrics)
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user metrics: {str(e)}", exc_info=True)
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateMetricsResponse(
                    status="error",
                    message="Error creating user metrics",
                    payload=str(e)
                ).dict()
            )
    
    def get_current_user_metrics(
        self, 
        db: Session, 
        authorization: str = Header(...)
    ):
        """
        Get user's current metrics
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            user_id = payload['user_id']
            
            # Get current metrics
            metrics = db.query(UserMetricsModel).filter(
                UserMetricsModel.user_id == user_id,
                UserMetricsModel.is_current == True
            ).first()
            
            if not metrics:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrieveMetricsResponse(
                        status="error",
                        message="No metrics found. Please create your profile first.",
                        payload="not_found"
                    ).dict()
                )
            
            return RetrieveMetricsResponse(
                status="success",
                message="Current user metrics",
                payload=UserMetricsRead.from_orm(metrics)
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving user metrics: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveMetricsResponse(
                    status="error",
                    message="Error retrieving user metrics",
                    payload=str(e)
                ).dict()
            )
    
    def update_user_metrics(
        self, 
        metrics_data: UserMetricsUpdate, 
        db: Session, 
        authorization: str = Header(...)
    ):
        """
        Update user metrics and recalculate TDEE
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            user_id = payload['user_id']
            
            # Get current metrics
            current_metrics = db.query(UserMetricsModel).filter(
                UserMetricsModel.user_id == user_id,
                UserMetricsModel.is_current == True
            ).first()
            
            if not current_metrics:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=UpdateMetricsResponse(
                        status="error",
                        message="No metrics found. Please create your profile first.",
                        payload="not_found"
                    ).dict()
                )
            
            # Update fields if provided
            if metrics_data.gender is not None:
                current_metrics.gender = metrics_data.gender
            if metrics_data.age is not None:
                current_metrics.age = metrics_data.age
            if metrics_data.weight_kg is not None:
                current_metrics.weight_kg = metrics_data.weight_kg
            if metrics_data.height_cm is not None:
                current_metrics.height_cm = metrics_data.height_cm
            if metrics_data.body_fat_percentage is not None:
                current_metrics.body_fat_percentage = metrics_data.body_fat_percentage
            if metrics_data.activity_level is not None:
                current_metrics.activity_level = metrics_data.activity_level
            
            # Recalculate TDEE
            tdee = TDEECalculator.calculate_tdee(
                weight_kg=current_metrics.weight_kg,
                body_fat_percentage=current_metrics.body_fat_percentage,
                activity_level=current_metrics.activity_level
            )
            current_metrics.calculated_tdee = tdee
            
            db.commit()
            db.refresh(current_metrics)
            
            return UpdateMetricsResponse(
                status="success",
                message=f"Metrics updated successfully. New TDEE: {tdee:.0f} kcal/day",
                payload=UserMetricsRead.from_orm(current_metrics)
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user metrics: {str(e)}", exc_info=True)
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=UpdateMetricsResponse(
                    status="error",
                    message="Error updating user metrics",
                    payload=str(e)
                ).dict()
            )