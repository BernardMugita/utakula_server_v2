# controllers/meal_plan_controller.py
import logging
from fastapi import HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid

from models.calorie_model import CalorieModel
from models.meal_plan_model import MealPlanModel
from models.meal_plan_day_model import MealPlanDayModel
from models.meal_plan_meal_model import MealPlanMealModel
from models.meal_plan_food_item_model import MealPlanFoodItemModel
from models.food_model import FoodModel
from models.user_model import UserModel
from models.user_metrics_model import UserMetricsModel

from schemas.calorie_schema import CalorieRead
from schemas.meal_plan_schema import (
    MealPlanPreferences, CreateMealPlanResponse, FetchMemberPlansResponse,
    MealPlanCreate, MealPlanRead, MealPlanUpdate, RetrieveMealPlanResponse,
    SharedMealPlanRead, SuggestMealPlanResponse, SuggestedMealPlan, UpdateMealPlanResponse
)
from schemas.food_schema import FoodRead

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

    # -------------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------------

    def _sort_day_plans(self, day_plans: list) -> list:
        """
        Sort a list of day plans (either models or dicts) chronologically 
        starting from Sunday.
        """
        day_order = {
            "Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3,
            "Thursday": 4, "Friday": 5, "Saturday": 6
        }
        
        return sorted(
            day_plans,
            key=lambda x: day_order.get(x["day"] if isinstance(x, dict) else x.day, 7)
        )

    def _populate_normalized_tables(self, db: Session, meal_plan_id: str, meal_plan_dict: list):
        """
        Given a meal_plan_id and the raw meal plan list (JSON blob structure),
        populate meal_plan_day -> meal_plan_meal -> meal_plan_food_item.
        Called on both create and update.
        """
        for day_data in meal_plan_dict:
            day_plan = MealPlanDayModel(
                id=str(uuid.uuid4()),
                meal_plan_id=meal_plan_id,
                day=day_data["day"],
                total_calories=day_data.get("total_calories", 0.0)
            )
            db.add(day_plan)
            db.flush()

            meals = day_data.get("meal_plan", {})

            for meal_type in ["breakfast", "lunch", "supper"]:
                food_list = meals.get(meal_type, [])
                if not food_list:
                    continue

                meal = MealPlanMealModel(
                    id=str(uuid.uuid4()),
                    day_plan_id=day_plan.id,
                    meal_type=meal_type
                )
                db.add(meal)
                db.flush()

                for food in food_list:
                    food_item = MealPlanFoodItemModel(
                        id=str(uuid.uuid4()),
                        meal_id=meal.id,
                        food_id=food["id"],
                        grams=food.get("grams", 0.0),
                        servings=food.get("servings", 1.0)
                    )
                    db.add(food_item)

    def _wipe_normalized_tables(self, db: Session, meal_plan_id: str):
        """
        Delete all normalized rows for a given meal_plan_id.
        Cascades handle meal_plan_meal and meal_plan_food_item automatically.
        """
        db.query(MealPlanDayModel).filter(
            MealPlanDayModel.meal_plan_id == meal_plan_id
        ).delete(synchronize_session=False)

    def _hydrate_meal_plan(self, db: Session, meal_plan: MealPlanModel) -> dict:
        """
        Build the response payload from the normalized tables, hydrating
        food data live from the foods table. Returns the same JSON structure
        the app already expects.
        """
        days_response = []

        # Sort day plans chronologically (Sunday to Saturday)
        sorted_day_plans = self._sort_day_plans(meal_plan.day_plans)

        for day_plan in sorted_day_plans:
            meals_response = {"breakfast": [], "lunch": [], "supper": []}
            total_macros = {"protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}

            for meal in day_plan.meals:
                for food_item in meal.food_items:
                    food = db.query(FoodModel).filter(
                        FoodModel.id == food_item.food_id
                    ).first()

                    if not food:
                        logger.warning(f"Food {food_item.food_id} not found — skipping.")
                        continue

                    # Calculate macros for this portion based on grams
                    ratio = food_item.grams / food.reference_portion_grams
                    breakdown = food.calories.breakdown

                    portion_macros = {
                        "protein_g": round(breakdown["protein"]["amount"] * ratio, 2),
                        "carbs_g": round(breakdown["carbohydrate"]["amount"] * ratio, 2),
                        "fat_g": round(breakdown["fat"]["amount"] * ratio, 2),
                        "fiber_g": round(breakdown["fiber"]["amount"] * ratio, 2),
                    }

                    total_calories_for_portion = round(
                        (food.calories.total / food.reference_portion_grams) * food_item.grams, 2
                    )

                    # Accumulate daily macros
                    for key in total_macros:
                        total_macros[key] = round(total_macros[key] + portion_macros[key], 2)

                    meals_response[meal.meal_type].append({
                        "id": food.id,
                        "name": food.name,
                        "grams": food_item.grams,
                        "servings": food_item.servings,
                        "image_url": food.image_url,
                        "calories_per_100g": round(
                            food.calories.total / food.reference_portion_grams * 100, 2
                        ),
                        "total_calories": total_calories_for_portion,
                        "macros": portion_macros
                    })

            days_response.append({
                "day": day_plan.day,
                "meal_plan": meals_response,
                "total_calories": day_plan.total_calories,
                "total_macros": total_macros
            })

        return {
            "id": meal_plan.id,
            "user_id": str(meal_plan.user_id),
            "members": meal_plan.members,
            "meal_plan": days_response
        }

    # -------------------------------------------------------------------------
    # ENDPOINTS
    # -------------------------------------------------------------------------

    def create_meal_plan(self, meal_plan_data: MealPlanCreate, db: Session, authorization: str = Header(...)):
        """
        Creates a new meal plan for a user.
        Saves to JSON blob (rollback) and populates normalized tables.
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
                MealPlanModel.user_id == payload['user_id']
            ).first()

            if existing_meal_plan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has a meal plan."
                )

            # Sort and convert to dict
            meal_plan_dict = [
                day.dict() for day in self._sort_day_plans(meal_plan_data.meal_plan)
            ]

            new_meal_plan = MealPlanModel(
                user_id=payload['user_id'],
                members=[],
                meal_plan=meal_plan_dict
            )

            db.add(new_meal_plan)
            db.flush()  # Get new_meal_plan.id before populating children

            self._populate_normalized_tables(db, new_meal_plan.id, meal_plan_dict)

            db.commit()
            db.refresh(new_meal_plan)

            return {
                "status": "success",
                "message": "Meal plan created successfully",
                "payload": self._hydrate_meal_plan(db, new_meal_plan)
            }

        except HTTPException:
            raise

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating meal plan: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateMealPlanResponse(
                    status="error",
                    message="Error when creating Meal plan!",
                    payload=str(e)
                ).dict()
            )

    def get_user_meal_plan(self, db: Session, authorization: str = Header(...)):
        """
        Get user's saved meal plan, hydrated with live food data.
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )

            token = authorization[7:]
            payload = utils.validate_JWT(token)

            meal_plan = db.query(MealPlanModel).filter(
                MealPlanModel.user_id == payload['user_id']
            ).first()

            if not meal_plan:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrieveMealPlanResponse(
                        status="error",
                        message="User does not have a meal plan!",
                        payload=[]
                    ).dict()
                )

            return {
                "status": "success",
                "message": "User's meal plan",
                "payload": self._hydrate_meal_plan(db, meal_plan)
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error fetching meal plan: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveMealPlanResponse(
                    status="error",
                    message="Error fetching Meal plan!",
                    payload=str(e)
                ).dict()
            )

    def update_user_meal_plan(self, db: Session, meal_plan_data: MealPlanUpdate, authorization: str):
        """
        Update user's meal plan.
        Wipes and rebuilds normalized tables. Updates JSON blob as rollback.
        """
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

            # Sort and convert to dict
            meal_plan_dict = [
                day.dict() for day in self._sort_day_plans(meal_plan_data.meal_plan)
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

            # Update JSON blob (rollback copy)
            meal_plan_info.meal_plan = meal_plan_dict

            # Wipe and rebuild normalized tables
            self._wipe_normalized_tables(db, meal_plan_info.id)
            db.flush()
            self._populate_normalized_tables(db, meal_plan_info.id, meal_plan_dict)

            db.commit()
            db.refresh(meal_plan_info)

            return {
                "status": "success",
                "message": "Meal plan updated successfully",
                "payload": self._hydrate_meal_plan(db, meal_plan_info)
            }

        except HTTPException:
            raise

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating meal plan: {str(e)}", exc_info=True)
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
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )

            token = authorization[7:]
            payload = utils.validate_JWT(token)

            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token: user_id not found in payload"
                )

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

            response_payload = []
            for plan in list_of_meal_plans:
                owner_user = db.query(UserModel).filter(
                    UserModel.id == plan.user_id
                ).first()

                if not owner_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Owner with user_id {plan.user_id} not found"
                    )

                hydrated = self._hydrate_meal_plan(db, plan)
                hydrated["owner"] = owner_user.username
                response_payload.append(hydrated)

            return {
                "status": "success",
                "message": "Meal plans retrieved successfully",
                "payload": response_payload
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error fetching member meal plans: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=FetchMemberPlansResponse(
                    status="error",
                    message="Error retrieving Meal Plans!",
                    payload=str(e)
                ).dict()
            )

    # -------------------------------------------------------------------------
    # SUGGESTION (unchanged — needs separate attention)
    # -------------------------------------------------------------------------

    async def suggest_meal_plan(
        self,
        meal_plan_preferences: MealPlanPreferences,
        db: Session,
        authorization: str = Header(...)
    ):
        """
        Suggests an intelligent meal plan based on TDEE or manual calorie target.
        Returns a preview — not saved to DB. User can pass the payload to
        /meal_plans/add_new_plan to save it.
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

            if meal_plan_preferences.body_goal not in BodyGoal.__members__:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid body goal. Must be one of: {', '.join(BodyGoal.__members__.keys())}"
                )

            calculated_tdee = None
            target_calories = None

            if meal_plan_preferences.use_calculated_tdee:
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

                calculated_tdee = user_metrics.calculated_tdee
                target_calories = TDEECalculator.adjust_for_body_goal(
                    calculated_tdee,
                    meal_plan_preferences.body_goal
                )
                logger.info(f"Using calculated TDEE: {calculated_tdee:.0f} kcal, adjusted to {target_calories:.0f} for {meal_plan_preferences.body_goal}")

            else:
                if not meal_plan_preferences.daily_calorie_target:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Daily calorie target is required when not using calculated TDEE."
                    )
                target_calories = float(meal_plan_preferences.daily_calorie_target)
                logger.info(f"Using manual calorie target: {target_calories:.0f} kcal")

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

            # Fetch and convert foods
            food_list = db.query(FoodModel).all()

            if not food_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No foods available in the database."
                )

            food_read_list = [
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

            logger.info(f"Loaded {len(food_read_list)} foods for user {user_id}")

            # Filter by dietary requirements
            filtered_foods = await MealPlanHelpers.filter_by_dietary_requirements(
                db,
                meal_plan_preferences.dietary_restrictions or [],
                meal_plan_preferences.allergies or [],
                meal_plan_preferences.medical_conditions or [],
                food_read_list
            )

            if not filtered_foods:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=SuggestMealPlanResponse(
                        status="warning",
                        message="No foods match your dietary requirements. Please adjust your preferences.",
                        payload=[]
                    ).dict()
                )

            logger.info(f"After dietary filtering: {len(filtered_foods)} foods available")

            # Generate the meal plan — returns list of day dicts with SelectedFood objects
            meal_plan = await MealPlanHelpers.generate_user_meal_plan(
                db,
                filtered_foods,
                target_calories,
                meal_plan_preferences.body_goal
            )

            # meal_plan is already in DayMealPlan-compatible shape:
            # [{ day, meal_plan: { breakfast, lunch, supper }, total_calories, total_macros }]
            # SelectedFood objects inside are Pydantic models — serializable directly.
            # The app can pass this payload straight to /meal_plans/add_new_plan. ✅

            return {
                "status": "success",
                "message": "Meal plan suggested successfully",
                "payload": {
                    "id": "",
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