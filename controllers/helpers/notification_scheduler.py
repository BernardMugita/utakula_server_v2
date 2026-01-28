from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, time as time_type
from models.notification_model import NotificationModel
from models.meal_plan_model import MealPlanModel
from models.user_model import UserModel
from controllers.helpers.notification_helpers import NotiticationHelpers
import logging
from firebase_admin import messaging
from connect import SessionLocal
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define timezone
TIMEZONE = pytz.timezone('Africa/Nairobi')  # East Africa Time (EAT)

class NotificationScheduler:
    def __init__(self):
        # Configure scheduler with timezone
        self.scheduler = BackgroundScheduler(timezone=TIMEZONE)
        self.notification_utils = NotiticationHelpers()
        
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Notification scheduler started")
        else:
            logger.info("Notification scheduler already running")
        
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Notification scheduler stopped")
        
    def schedule_user_notifications(self, user_id: str, device_token: str, notification_settings: dict):
        """
        Schedule notifications for a specific user based on their settings
        
        Args:
            user_id: The user's ID
            notification_settings: Dict containing notification settings
        """
        # Remove existing jobs for this user
        self.remove_user_notifications(user_id)
        
        # Schedule notifications for each meal
        for meal_notif in notification_settings['notification_for']:
            meal_time = meal_notif['meal_time']  
            meal = meal_notif['meal']  # e.g., "breakfast"
            
            # Parse the meal time - handle both time objects and strings
            if isinstance(meal_time, time_type):
                # Already a time object
                hour = meal_time.hour
                minute = meal_time.minute
            elif isinstance(meal_time, str):
                # Parse string format
                if ':' in meal_time:
                    # Handle "08:00" or "08:00:00" format
                    parts = meal_time.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                else:
                    # Handle "0800" format
                    hour = int(meal_time[:2])
                    minute = int(meal_time[2:4]) if len(meal_time) >= 4 else 0
            else:
                logger.error(f"Unexpected meal_time type: {type(meal_time)}")
                continue
            
            # Calculate notification time based on time_before_meals
            time_before = notification_settings['time_before_meals']  # hours
            
            # Calculate frequency (how many notifications before the meal)
            frequency = notification_settings['frequency_before_meals']
            
            # Schedule multiple notifications based on frequency
            for i in range(frequency):
                hours_before = time_before - (i * (time_before / frequency))
                notif_hour = int((hour - hours_before) % 24)
                
                job_id = f"user_{user_id}_meal_{meal}_notif_{i}"
                
                self.scheduler.add_job(
                    func=self._send_scheduled_notification,
                    trigger=CronTrigger(hour=notif_hour, minute=minute, timezone=TIMEZONE),
                    args=[user_id, device_token, meal],
                    id=job_id,
                    replace_existing=True
                )
                
                logger.info(f"✅ Scheduled notification for user {user_id}, meal: {meal} at {notif_hour}:{minute:02d} EAT")
    
    def remove_user_notifications(self, user_id: str):
        """Remove all scheduled notifications for a user"""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"user_{user_id}_"):
                self.scheduler.remove_job(job.id)
                logger.info(f"Removed job: {job.id}")
    
    def _send_scheduled_notification(self, user_id: str, device_token: str, meal: str):
        """
        Internal method to send a notification (called by scheduler)
        
        Args:
            user_id: The user's ID
            device_token: User's FCM device token
            meal: The meal name (breakfast, lunch, supper)
        """
        db = SessionLocal()
        try:
            logger.info(f"🔔 Sending notification for user {user_id}, meal: {meal}")
            
            # Get user's meal plan
            existing_meal_plan = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == user_id
            ).first()
            
            if not existing_meal_plan:
                logger.warning(f"⚠️ No meal plan found for user {user_id}")
                return
            
            # Get current day of the week in EAT timezone
            now_eat = datetime.now(TIMEZONE)
            day_of_the_week = now_eat.strftime("%A").lower()
            
            logger.info(f"📅 Current day: {day_of_the_week}")
            
            # Get meals for today
            day_meal_foods = [
                meal_data['meal_plan'] for meal_data in existing_meal_plan.meal_plan 
                if meal_data['day'].lower() == day_of_the_week
            ]
            
            if not day_meal_foods:
                logger.warning(f"⚠️ No meals found for {day_of_the_week}")
                return
            
            # Get foods for the specific meal
            meal_dict = day_meal_foods[0]
            meal_foods = meal_dict.get(meal.lower(), [])
            
            if not meal_foods:
                logger.warning(f"⚠️ No foods found for meal: {meal}")
                return
            
            logger.info(f"🍽️ Found {len(meal_foods)} foods for {meal}")
            
            # Send the notification
            notification = self.notification_utils.send_notification(
                meal=meal.capitalize(),
                meal_foods=meal_foods,
                is_authorized=True
            )
            
            logger.info(f"📧 Notification prepared: {notification.notification_title}")
            
            # Validate device token
            if not device_token or device_token == "":
                logger.error(f"❌ Invalid device token for user {user_id}")
                return
            
            # Send message via Firebase
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.notification_title,
                    body=notification.notification_message
                ),
                data={
                    "food_images": ",".join(notification.food_images) if notification.food_images else "",
                    "notification_time": notification.notification_time,
                    "meal": meal
                },
                token=device_token
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Firebase message sent to user {user_id}, response: {response}")
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {str(e)}", exc_info=True)
        finally:
            db.close()

    def reload_all_user_notifications(self, db: Session):
        """Reload all users' notification settings on scheduler startup"""
        try:
            logger.info("🔄 Reloading all user notification schedules...")
            
            # Get all users with notification settings
            all_settings = db.query(NotificationModel).filter(
                NotificationModel.notifications_enabled == True
            ).all()
            
            logger.info(f"📋 Found {len(all_settings)} users with enabled notifications")
            
            for settings in all_settings:
                # Get user's device token
                user = db.query(UserModel).filter(
                    UserModel.id == settings.user_id
                ).first()
                
                if user and user.device_token:
                    self.schedule_user_notifications(
                        user_id=user.id,
                        device_token=user.device_token,
                        notification_settings={
                            'time_before_meals': settings.time_before_meals,
                            'frequency_before_meals': settings.frequency_before_meals,
                            'notification_for': settings.notification_for
                        }
                    )
                    logger.info(f"✅ Scheduled notifications for user {user.id}")
                else:
                    logger.warning(f"⚠️ User {settings.user_id} has no device token")
            
            logger.info(f"✅ Reloaded notifications for {len(all_settings)} users")
            
            # Log all scheduled jobs
            jobs = self.scheduler.get_jobs()
            logger.info(f"📊 Total scheduled jobs: {len(jobs)}")
            for job in jobs:
                logger.info(f"  - {job.id}: next run at {job.next_run_time}")
                
        except Exception as e:
            logger.error(f"❌ Error reloading notifications: {e}", exc_info=True)

# Create a global scheduler instance
notification_scheduler = NotificationScheduler()