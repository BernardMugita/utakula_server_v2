from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from models.user_model import UserModel
from models.calorie_model import CalorieModel
from models.food_model import FoodModel
from models.meal_plan_model import MealPlanModel
from models.notification_model import NotificationModel
from models.user_metrics_model import UserMetricsModel