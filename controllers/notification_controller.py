from fastapi import HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.meal_plan_model import MealPlanModel
from models.user_model import UserModel
from models.notification_model import NotificationModel
from schemas.notification_schema import MealPlanNotification, NotificationSettings, NotificationHandlerResponse
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
                existing_settings.time_before_meals = notification_settings.time_before_meals
                existing_settings.frequency_before_meals = notification_settings.frequency_before_meals
                existing_settings.notification_for = notification_for_dict
                settings = existing_settings
            else:
                # Create new settings
                settings = NotificationModel(
                    user_id=exiting_user.id,
                    time_before_meals=notification_settings.time_before_meals,
                    frequency_before_meals=notification_settings.frequency_before_meals,
                    notification_for=notification_for_dict
                )
                db.add(settings)
            
            db.commit()
            db.refresh(settings)
            
            # Schedule notifications for this user
            notification_scheduler.schedule_user_notifications(
                user_id=exiting_user.id,
                device_token=exiting_user.device_token,
                notification_settings={
                    'time_before_meals': settings.time_before_meals,
                    'frequency_before_meals': settings.frequency_before_meals,
                    'notification_for': settings.notification_for
                }
            )

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

    def send_notification_handler(
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
            
            existing_meal_plan = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == payload['user_id']).first()
            
            if not existing_meal_plan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No meal plan found for the user."
                )
            
            notification_settings = db.query(NotificationModel).filter(
                NotificationModel.user_id == payload['user_id']
            ).first()
            
            if not notification_settings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Set notification settings before sending notifications."
                )
            
            day_of_the_week = datetime.now().strftime("%A").lower()
            day_meal_foods = [
                meal['meal_plan'] for meal in existing_meal_plan.meal_plan 
                if meal['day'].lower() == day_of_the_week
            ]
            
            time_of_the_day = datetime.now().hour
            most_relevant_meal = [
                meal_notification for meal_notification in notification_settings.notification_for
                if abs(int(meal_notification['meal_time'].split(':')[0]) - time_of_the_day) <= notification_settings.time_before_meals
            ]
            
            meal = most_relevant_meal[0]['meal'].capitalize() if most_relevant_meal else None
            
            if not meal:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=NotificationHandlerResponse(
                        status="success",
                        message="No relevant meal found for current time.",
                        payload=None
                    ).model_dump()
                )
            
            meal_foods = []
            if day_meal_foods:
                meal_dict = day_meal_foods[0]
                meal_foods = meal_dict.get(meal.lower(), [])
            
            new_notification = notification_utils.send_notification(
                meal=meal,
                meal_foods=meal_foods,
                is_authorized=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=NotificationHandlerResponse(
                    status="success",
                    message="Notification sent successfully.",
                    payload=new_notification
                ).model_dump()
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=NotificationHandlerResponse(
                    status="error",
                    message="Failed to send notification: " + str(e),
                    payload=None
                ).model_dump()
            )