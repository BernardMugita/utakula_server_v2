from schemas.notification_schema import MealPlanNotification, NotificationFoods, NotificationHandlerResponse
from fastapi.responses import JSONResponse
from fastapi import status
from schemas.notification_schema import MealEnum
from datetime import datetime

class NotiticationHelpers:
    pass

    @staticmethod
    @staticmethod
    def send_notification(
        meal: MealEnum,
        meal_foods: list[NotificationFoods],
        is_authorized: bool
    ) -> MealPlanNotification | str:
        try:
            if not is_authorized:
                return MealPlanNotification(
                        notification_time=datetime.now().isoformat() + "Z",
                        notification_title="Unauthorized",
                        notification_message="You are not authorized to receive this notification.",
                        food_images=[]
                    )
                
            notification_foods = [
                food['name'] for food in meal_foods
            ]
            
            print("Notification Foods:", notification_foods)
            
            notification_images = [
                food['image_url'] for food in meal_foods
            ]
            
            print("Notification Images:", notification_images)

            # Format the food list as "food1, food2 & food3"
            if len(notification_foods) == 0:
                foods_text = "no foods"
            elif len(notification_foods) == 1:
                foods_text = notification_foods[0]
            elif len(notification_foods) == 2:
                foods_text = f"{notification_foods[0]} & {notification_foods[1]}"
            else:
                foods_text = ", ".join(notification_foods[:-1]) + f" & {notification_foods[-1]}"

            notification_time = datetime.now().isoformat() + "Z"
            notification_title = f"{meal} Reminder"
            notification_message = f"You have {foods_text} for {meal}."
            
            return MealPlanNotification(
                        notification_time=notification_time,
                        notification_title=notification_title,
                        notification_message=notification_message,
                        food_images=notification_images
                    )

        except Exception as e:
            return f"An error occurred while sending notification: {str(e)}"