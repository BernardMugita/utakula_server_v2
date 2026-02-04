import json
from fastapi import HTTPException, Header, logger, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.meal_plan_model import MealPlanModel
from models.user_model import UserModel
from models.notification_model import NotificationModel
from schemas.notification_schema import NotificationFor, NotificationSettings, NotificationHandlerResponse, NotificationsTestSchema, SendNotificationRequest
from controllers.helpers.notification_helpers import NotiticationHelpers
from utils.helper_utils import HelperUtils
from controllers.helpers.notification_scheduler import NotificationScheduler
from datetime import datetime
from firebase_admin import messaging
from schemas.notification_schema import NotificationsTestSchema

notification_utils = NotiticationHelpers()
utils = HelperUtils()
notification_scheduler = NotificationScheduler()

class NotificationController:
    def __init__(self) -> None:
        pass
    
    def test_notification(self, testSchema: NotificationsTestSchema, db: Session):
        user = db.query(UserModel).filter(UserModel.id == testSchema.user_id).first()
    
        if not user or not user.device_token:
            return {"error": "User or token not found"}
        
        print(user.device_token)
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="Test Notification",
                body="Testing FCM"
            ),
            token=user.device_token
        )
        
        print(message)
        
        try:
            response = messaging.send(message)
            return {"success": True, "response": response}
        except Exception as e:
            print(e)
            return {"error": str(e)}
        finally:
            db.close()
            
    def send_meal_notification(
        self, 
        db: Session,
        request: SendNotificationRequest,
        authorization: str = Header(...)
    ):
        """
        Send a notification for a specific meal
        Called by Flutter local notifications
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
            
            # Send notification
            result = notification_scheduler._send_scheduled_notification(
                user_id=user_id,
                meal=request.meal
            )
            
            print(result.get("notification"))
            
            if result.get("success"):
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=NotificationHandlerResponse(
                        status="success",
                        message="Notification sent successfully.",
                        payload=result.get("notification")
                    ).model_dump()
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=NotificationHandlerResponse(
                        status="error",
                        message=result.get("error", "Failed to send notification"),
                        payload=None
                    ).model_dump()
                )
                
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=NotificationHandlerResponse(
                    status="error",
                    message=f"Failed to send notification: {str(e)}",
                    payload=None
                ).model_dump()
            )

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
                    },
                    db=db
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
            
    
    def get_scheduled_notifications(
        self,
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
            
            jobs = notification_scheduler.scheduler.get_jobs()
            
            # Filter jobs for the current user
            user_jobs = [
                job for job in jobs 
                if f"user_{payload['user_id']}" in job.id
            ]
            
            jobs_list = []
            for job in user_jobs:
                try:
                    # Get next run time safely
                    next_run = None
                    if hasattr(job, 'next_run_time') and job.next_run_time:
                        next_run = job.next_run_time.isoformat()
                    elif hasattr(job, 'trigger'):
                        # Try to get next fire time from trigger
                        next_fire = job.trigger.get_next_fire_time(None, datetime.now())
                        if next_fire:
                            next_run = next_fire.isoformat()
                    
                    jobs_list.append({
                        "id": job.id,
                        "next_run_time": next_run,
                        "func_name": job.func.__name__ if hasattr(job, 'func') else None,
                        "trigger": str(job.trigger) if hasattr(job, 'trigger') else None,
                    })
                except Exception as e:
                    continue
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Scheduled notifications retrieved successfully.",
                    "payload": {
                        "total_jobs": len(jobs_list),
                        "scheduler_running": notification_scheduler.scheduler.running,
                        "jobs": jobs_list
                    }
                }
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=NotificationHandlerResponse(
                    status="error",
                    message=f"Failed to retrieve scheduled notifications: {str(e)}",
                    payload=None
                ).model_dump()
            )