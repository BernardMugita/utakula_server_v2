from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from routes.user_metrics_routes import router as user_metrics_router
from routes.food_routes import router as food_router
from routes.calorie_routes import router as calorie_router
from routes.meal_plan_routes import router as meal_plan_router
from routes.invitation_routes import router as invitation_router
# from routes.genai_routes import router as genai_router
from routes.notification_routes import router as notification_router
from routes.membership_routes import router as membership_router
from routes.payment_routes import router as payment_router
from routes.subscription_routes import router as subscription_router
from controllers.helpers.notification_scheduler import NotificationScheduler
from utils.helper_utils import HelperUtils
from connect import SessionLocal
import logging

# Setup logger
logger = logging.getLogger(__name__)

helper_utils = HelperUtils()
helper_utils.initialize_firebase()
notification_scheduler = NotificationScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    notification_scheduler.start()
    logger.info("✅ Notification scheduler started")
    print("Notification scheduler started")
    
    # Reload all user notification schedules
    db = SessionLocal()
    try:
        logger.info("🔄 Reloading user notification schedules...")
        notification_scheduler.reload_all_user_notifications(db)
        logger.info("✅ User notification schedules reloaded")
    except Exception as e:
        logger.error(f"❌ Error reloading notification schedules: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    notification_scheduler.stop()
    logger.info("❌ Notification scheduler stopped")
    print("Notification scheduler stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Where is the food"}

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(user_metrics_router)
app.include_router(food_router)
app.include_router(calorie_router)
app.include_router(meal_plan_router)
app.include_router(notification_router)
app.include_router(invitation_router)
# app.include_router(genai_router)
app.include_router(membership_router)
app.include_router(payment_router)
app.include_router(subscription_router)