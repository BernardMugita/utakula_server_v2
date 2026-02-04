from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session

from connect import SessionLocal
from controllers.notification_controller import NotificationController
from models.user_model import UserModel
from schemas.notification_schema import NotificationHandlerResponse, NotificationSettings, SendNotificationRequest
from firebase_admin import messaging
from schemas.notification_schema import NotificationsTestSchema

router = APIRouter()
notification_controller = NotificationController()

# Dependency to get the SQLAlchemy session
def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/notifications/send", response_model=NotificationHandlerResponse)
def send_notification(
    db: Session = Depends(get_db_connection),
    request: SendNotificationRequest = Body(...),
    authorization: str = Header(...),
):
    return notification_controller.send_meal_notification(
        db=db,
        request=request,
        authorization=authorization
    )
    
@router.post("/notifications/save_settings", response_model=NotificationHandlerResponse)
def set_notification_settings(
    db: Session = Depends(get_db_connection),
    notification_settings: NotificationSettings = Body(...),
    authorization: str = Header(...),
):
    return notification_controller.set_user_notification_settings(
        db=db,
        notification_settings=notification_settings,
        authorization=authorization
    )
    
@router.post("/notifications/get_notification_settings", response_model=NotificationHandlerResponse)
def get_notification_settings(
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...),
):
    return notification_controller.get_user_notification_settings(
        db=db,
        authorization=authorization
    )
    
@router.post("/notifications/get_scheduled_jobs")
def get_scheduled_jobs(
    authorization: str = Header(...),
):
    return notification_controller.get_scheduled_notifications(
        authorization=authorization
    )
    
# Create a test endpoint to verify the token works
@router.post("/notifications/test-notification")
async def test_notification(testSchema: NotificationsTestSchema, db: Session = Depends(get_db_connection)):
    return notification_controller.test_notification(
        db=db,
        testSchema=testSchema
    )