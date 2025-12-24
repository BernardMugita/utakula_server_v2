import json
from fastapi import HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.meal_plan_model import MealPlanModel
from models.user_model import UserModel
from models.notification_model import NotificationModel
from schemas.notification_schema import MealPlanNotification, NotificationFor, NotificationSettings, NotificationHandlerResponse
from controllers.helpers.notification_helpers import NotiticationHelpers
from utils.helper_utils import HelperUtils
from controllers.helpers.notification_scheduler import NotificationScheduler
from datetime import datetime

notification_utils = NotiticationHelpers()
utils = HelperUtils()
notification_scheduler = NotificationScheduler()

class NotificationController:
    def __init__(self) -> None:
        pass

    def set_user_notification_settings(
        self, 
        db: Session, 
        notification_settings: NotificationSettings, 
        authorization: str = Header(...)
    ):
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            exiting_user = db.query(UserModel).filter(
                UserModel.id == payload['user_id']
            ).first()
            
            if not exiting_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )

            if notification_settings.time_before_meals is None \
                or notification_settings.frequency_before_meals is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Notification settings must include time_before_meals and frequency_before_meals."
                )

            # Convert Pydantic models to JSON-serializable dictionaries
            notification_for_dict = [notif.model_dump(mode='json') for notif in notification_settings.notification_for]

            # Check if settings already exist
            existing_settings = db.query(NotificationModel).filter(
                NotificationModel.user_id == exiting_user.id
            ).first()
            
            if existing_settings:
                # Update existing settings
                existing_settings.notifications_enabled = notification_settings.notifications_enabled  # Add this
                existing_settings.time_before_meals = notification_settings.time_before_meals
                existing_settings.frequency_before_meals = notification_settings.frequency_before_meals
                existing_settings.notification_for = notification_for_dict
                settings = existing_settings
            else:
                # Create new settings
                settings = NotificationModel(
                    user_id=exiting_user.id,
                    notifications_enabled=notification_settings.notifications_enabled,  # Use from request
                    time_before_meals=notification_settings.time_before_meals,
                    frequency_before_meals=notification_settings.frequency_before_meals,
                    notification_for=notification_for_dict
                )
                db.add(settings)
            
            db.commit()
            db.refresh(settings)
            
            # Only schedule notifications if enabled
            if settings.notifications_enabled:
                notification_scheduler.schedule_user_notifications(
                    user_id=exiting_user.id,
                    device_token=exiting_user.device_token,
                    notification_settings={
                        'time_before_meals': settings.time_before_meals,
                        'frequency_before_meals': settings.frequency_before_meals,
                        'notification_for': settings.notification_for
                    }
                )
            else:
                # Remove scheduled notifications if disabled
                notification_scheduler.remove_user_notifications(exiting_user.id)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=NotificationHandlerResponse(
                    status="success",
                    message="Notification settings updated and scheduled successfully.",
                    payload=None
                ).model_dump()
            )

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=NotificationHandlerResponse(
                    status="error",
                    message="Failed to update notification settings: " + str(e),
                    payload=None
                ).model_dump()
            )


    def get_user_notification_settings(
        self,
        db: Session,
        authorization: str = Header(...)
    ):
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            existing_settings = db.query(NotificationModel).filter(
                NotificationModel.user_id == payload['user_id']
            ).first()
            
            if not existing_settings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification settings not found for the user."
                )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=NotificationHandlerResponse(
                    status="success",
                    message="Notification settings retrieved successfully.",
                    payload=NotificationSettings(
                        notifications_enabled=existing_settings.notifications_enabled,  # ADD THIS LINE
                        time_before_meals=existing_settings.time_before_meals,
                        frequency_before_meals=existing_settings.frequency_before_meals,
                        notification_for=[
                            NotificationFor(
                                meal=notif['meal'],
                                meal_time=notif['meal_time']
                            ) for notif in existing_settings.notification_for
                        ]
                    )
                ).model_dump()
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=NotificationHandlerResponse(
                    status="error",
                    message="Failed to retrieve notification settings: " + str(e),
                    payload=None
                ).model_dump()
            )