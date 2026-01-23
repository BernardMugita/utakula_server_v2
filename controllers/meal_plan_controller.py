# controllers/meal_plan_controller.py
import asyncio
import logging
from fastapi import HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.calorie_model import CalorieModel
from models.meal_plan_model import MealPlanModel
from models.user_model import UserModel
from models.user_metrics_model import UserMetricsModel
from schemas.calorie_schema import CalorieRead
from schemas.meal_plan_schema import (
    MealPlanPreferences, CreateMealPlanResponse, FetchMemberPlansResponse, 
    MealPlanCreate, MealPlanRead, MealPlanUpdate, RetrieveMealPlanResponse, 
    SharedMealPlanRead, SuggestMealPlanResponse, SuggestedMealPlan, UpdateMealPlanResponse
)
from schemas.food_schema import FoodRead

from models.food_model import FoodModel
from utils.helper_utils import HelperUtils
from controllers.helpers.meal_plan_helpers import MealPlanHelpers
from controllers.helpers.tdee_calculator import TDEECalculator
from utils.enums import BodyGoal

utils = HelperUtils()

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/logs.log', level=logging.INFO)

class MealPlanController:
    def __init__(self) -> None:
        pass
    
    def create_meal_plan(self, meal_plan_data: MealPlanCreate, db: Session, authorization: str = Header(...)):
        """
        Creates a new meal plan for a user.
        This is for MANUAL meal plan creation where users select their own foods.
        Foods should already have grams and servings calculated.
        """
        
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
            
            if existing_meal_plan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has a meal plan."
                )

            # Convert meal plan to a JSON-serializable format
            meal_plan_dict = [
                day_meal_plan.dict() for day_meal_plan in meal_plan_data.meal_plan
            ]
            
            # Create an instance of MealPlanModel
            new_meal_plan = MealPlanModel(
                user_id=payload['user_id'],
                members=[],
                meal_plan=meal_plan_dict
            )
            
            db.add(new_meal_plan)
            db.commit()
            db.refresh(new_meal_plan)
            
            return {
                "status": "success",
                "message": "Meal plan created successfully",
                "payload": new_meal_plan
            }
          
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateMealPlanResponse(
                    status="error",
                    message="Error when creating Meal plan!",
                    payload=str(e)
                ).dict()
            )
            
    async def suggest_meal_plan(
        self, 
        meal_plan_preferences: MealPlanPreferences, 
        db: Session, 
        authorization: str = Header(...)
    ):
        """
        Suggests an intelligent meal plan for a user based on TDEE or manual calorie target
        """
        
        try:
            # Validate authorization
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
                
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            user_id = payload['user_id']
            
            # Validate body goal
            if meal_plan_preferences.body_goal not in BodyGoal.__members__:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid body goal provided. Must be one of: {', '.join(BodyGoal.__members__.keys())}"
                )
            
            # Determine calorie target
            calculated_tdee = None
            target_calories = None
            
            if meal_plan_preferences.use_calculated_tdee:
                # Get user's current metrics
                user_metrics = db.query(UserMetricsModel).filter(
                    UserMetricsModel.user_id == user_id,
                    UserMetricsModel.is_current == True
                ).first()
                
                if not user_metrics:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content=SuggestMealPlanResponse(
                            status="error",
                            message="No user metrics found. Please complete your profile first or provide a manual calorie target.",
                            payload=[]
                        ).dict()
                    )
                
                # Use stored TDEE and adjust for body goal
                calculated_tdee = user_metrics.calculated_tdee
                target_calories = TDEECalculator.adjust_for_body_goal(
                    calculated_tdee,
                    meal_plan_preferences.body_goal
                )
                
                logger.info(f"Using calculated TDEE: {calculated_tdee:.0f} kcal/day, adjusted to {target_calories:.0f} for {meal_plan_preferences.body_goal}")
            
            else:
                # Use manual calorie target
                if not meal_plan_preferences.daily_calorie_target:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Daily calorie target is required when not using calculated TDEE."
                    )
                
                target_calories = meal_plan_preferences.daily_calorie_target
                logger.info(f"Using manual calorie target: {target_calories:.0f} kcal/day")
            
            # Validate calorie target
            if target_calories < 1200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Daily calorie target should be at least 1200 calories for health safety."
                )
            
            if target_calories > 5000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Daily calorie target seems unusually high. Please verify."
                )
            
            # Fetch all foods from database
            food_list = db.query(FoodModel).all()
            
            if not food_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No foods available in the database. Please add foods first."
                )
            
            # Convert to FoodRead schema
            food_list = [
                FoodRead(
                    food_id=food.id,
                    name=food.name,
                    calories=CalorieRead(
                        calorie_id=food.calories.id,
                        food_id=food.calories.food_id,
                        total=food.calories.total,
                        breakdown=food.calories.breakdown
                    ),  
                    reference_portion_grams=food.reference_portion_grams,
                    dietary_tags=food.dietary_tags,
                    allergens=food.allergens,
                    suitable_for_conditions=food.suitable_for_conditions,
                    image_url=food.image_url,
                    macro_nutrient=food.macro_nutrient,
                    meal_type=food.meal_type
                ) for food in food_list
            ]
            
            logger.info(f"Processing meal plan for user: {user_id}")
            logger.info(f"Body Goal: {meal_plan_preferences.body_goal}, Target Calories: {target_calories:.0f} kcal")
            
            # Filter by dietary requirements
            filtered_foods = await MealPlanHelpers.filter_by_dietary_requirements(
                db, 
                meal_plan_preferences.dietary_restrictions or [],
                meal_plan_preferences.allergies or [],
                meal_plan_preferences.medical_conditions or [],
                food_list
            )
            
            if not filtered_foods:
                return {
                    "status": "warning",
                    "message": "No foods match your dietary requirements. Please adjust your preferences or add more foods to the database.",
                    "payload": []
                }
            
            logger.info(f"After dietary filtering: {len(filtered_foods)} foods available")
            
            # Generate meal plan
            meal_plan = await MealPlanHelpers.generate_user_meal_plan(
                db,
                filtered_foods,
                target_calories,
                meal_plan_preferences.body_goal
            )
            
            return {
                "status": "success",
                "message": "Meal plan suggested successfully",
                "payload": {
                    "id": '',
                    "members": [],
                    "meal_plan": meal_plan,
                    "calculated_tdee": calculated_tdee,
                    "target_calories": target_calories
                }
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Error in suggest_meal_plan: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=SuggestMealPlanResponse(
                    status="error",
                    message="Error when suggesting meal plan!",
                    payload=str(e)
                ).dict()
            )
    
    def get_user_meal_plan(self, db: Session, authorization: str = Header(...)):
        """Get user's saved meal plan"""
        
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
                
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            meal_plan = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == payload['user_id']).first()
            
            if not meal_plan:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrieveMealPlanResponse(
                        status="error",
                        message="User does not have meal plan!",
                        payload=[]
                    ).dict()
                )
            
            return {
                "status": "success",
                "message": "User's meal plan",
                "payload": meal_plan
            }
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveMealPlanResponse(
                    status="error",
                    message="Error fetching Meal plan!",
                    payload=str(e)
                ).dict()
            )
            
    def update_user_meal_plan(self, db: Session, meal_plan_data: MealPlanUpdate, authorization: str):
        """Update user's meal plan"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
                
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            meal_plan_info = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == payload['user_id']
            ).first()
            
            if not meal_plan_info:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=UpdateMealPlanResponse(
                        status="error",
                        message="Error fetching Meal plan!",
                        payload="User does not have a meal plan."
                    ).dict()
                )
                
            meal_plan_dict = [
                day_meal_plan.dict() for day_meal_plan in meal_plan_data.meal_plan
            ]
            
            if meal_plan_dict == meal_plan_info.meal_plan:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=UpdateMealPlanResponse(
                        status="error",
                        message="Error updating Meal plan!",
                        payload="No changes were made to the meal plan."
                    ).dict()
                )                
                
            meal_plan_info.meal_plan = meal_plan_dict
            
            # Convert to MealPlanRead model for the response
            updated_meal_plan = MealPlanRead(
                id=meal_plan_info.id,
                user_id=meal_plan_info.user_id,
                members=meal_plan_info.members,
                meal_plan=meal_plan_dict
            )
            
            db.commit()
            db.refresh(meal_plan_info)  
            
            return {
                "status": "success",
                "message": "Meal plan updated successfully",
                "payload": updated_meal_plan
            }

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=UpdateMealPlanResponse(
                    status="error",
                    message="Error updating Meal plan!",
                    payload=str(e)
                ).dict()
            )
    
    def get_member_meal_plans(self, db: Session, authorization: str = Header(...)):
        """Retrieve meal plans shared with the logged-in user."""
        try:
            # Validate the authorization header
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )

            # Extract and validate the token
            token = authorization[7:]
            payload = utils.validate_JWT(token)

            # Extract user_id from the payload
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token: user_id not found in payload"
                )

            # Query meal plans where user_id is in the members list
            list_of_meal_plans = db.query(MealPlanModel).filter(
                MealPlanModel.members.contains(user_id)
            ).all()

            if not list_of_meal_plans:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=FetchMemberPlansResponse(
                        status="error",
                        message="No meal plans found for this user!",
                        payload="404"
                    ).dict()
                )

            # Fetch the username for each meal plan's owner (user_id)
            response_payload = []
            for plan in list_of_meal_plans:
                owner_user = db.query(UserModel).filter(UserModel.id == plan.user_id).first()
                if not owner_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Owner with user_id {plan.user_id} not found"
                    )

                response_payload.append(
                    SharedMealPlanRead(
                        id=plan.id,
                        user_id=plan.user_id,
                        owner=owner_user.username,
                        members=plan.members,
                        meal_plan=plan.meal_plan
                    )
                )

            # Construct and return the response
            return {
                "status": "success",
                "message": "Meal plans retrieved successfully",
                "payload": response_payload,
            }

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=FetchMemberPlansResponse(
                    status="error",
                    message="Error retrieving Meal Plans!",
                    payload=str(e)
                ).dict()
            )