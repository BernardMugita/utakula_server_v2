from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime
from models.notification_model import NotificationModel
from models.meal_plan_model import MealPlanModel
from controllers.helpers.notification_helpers import NotiticationHelpers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notification_utils = NotiticationHelpers()
        
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Notification scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Notification scheduler stopped")
        
    def schedule_user_notifications(self, user_id: str, notification_settings: dict):
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
            meal_time = meal_notif['meal_time']  # e.g., "08:00:00"
            meal = meal_notif['meal']  # e.g., "breakfast"
            
            # Parse the meal time
            hour, minute, _ = map(int, meal_time.split(':'))
            
            # Calculate notification time based on time_before_meals
            time_before = notification_settings['time_before_meals']  # hours
            notification_hour = (hour - time_before) % 24
            
            # Calculate frequency (how many notifications before the meal)
            frequency = notification_settings['frequency_before_meals']
            
            # Schedule multiple notifications based on frequency
            for i in range(frequency):
                hours_before = time_before - (i * (time_before / frequency))
                notif_hour = int((hour - hours_before) % 24)
                
                job_id = f"user_{user_id}_meal_{meal}_notif_{i}"
                
                # Schedule the job
                self.scheduler.add_job(
                    func=self._send_scheduled_notification,
                    trigger=CronTrigger(hour=notif_hour, minute=minute),
                    args=[user_id, meal],
                    id=job_id,
                    replace_existing=True
                )
                
                logger.info(f"Scheduled notification for user {user_id}, meal: {meal} at {notif_hour}:{minute:02d}")
    
    def remove_user_notifications(self, user_id: str):
        """Remove all scheduled notifications for a user"""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"user_{user_id}_"):
                self.scheduler.remove_job(job.id)
                logger.info(f"Removed job: {job.id}")
    
    def _send_scheduled_notification(self, user_id: str, meal: str):
        """
        Internal method to send a notification (called by scheduler)
        
        Args:
            user_id: The user's ID
            meal: The meal name (breakfast, lunch, supper)
        """
        db = Session()
        try:
            logger.info(f"Sending notification for user {user_id}, meal: {meal}")
            
            # Get user's meal plan
            existing_meal_plan = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == user_id
            ).first()
            
            if not existing_meal_plan:
                logger.warning(f"No meal plan found for user {user_id}")
                return
            
            # Get current day of the week
            day_of_the_week = datetime.now().strftime("%A").lower()
            
            # Get meals for today
            day_meal_foods = [
                meal_data['meal_plan'] for meal_data in existing_meal_plan.meal_plan 
                if meal_data['day'].lower() == day_of_the_week
            ]
            
            if not day_meal_foods:
                logger.warning(f"No meals found for {day_of_the_week}")
                return
            
            # Get foods for the specific meal
            meal_dict = day_meal_foods[0]
            meal_foods = meal_dict.get(meal.lower(), [])
            
            if not meal_foods:
                logger.warning(f"No foods found for meal: {meal}")
                return
            
            # Send the notification
            notification = self.notification_utils.send_notification(
                meal=meal.capitalize(),
                meal_foods=meal_foods,
                is_authorized=True
            )
            
            logger.info(f"Notification sent successfully: {notification}")
            
            # TODO: Send the notification via:
            # - In-app notification
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
        finally:
            db.close()

# Create a global scheduler instance
notification_scheduler = NotificationScheduler()