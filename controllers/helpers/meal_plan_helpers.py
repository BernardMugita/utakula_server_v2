import logging
import random
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from models.food_model import FoodModel
from schemas.calorie_schema import FoodRead
from schemas.meal_plan_schema import SelectedFood
from utils.enums import BodyGoal

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/logs.log', level=logging.INFO)

class MealPlanHelpers:
    
    # Calorie distribution percentages by body goal
    CALORIE_DISTRIBUTION = {
        BodyGoal.WEIGHT_LOSS.name: {
            "breakfast": 0.30, 
            "lunch": 0.35,    
            "supper": 0.30,    
            "snacks": 0.05,   
            "adjustment": -0.10 
        },
        BodyGoal.MUSCLE_GAIN.name: {
            "breakfast": 0.25,
            "lunch": 0.35,
            "supper": 0.30,
            "snacks": 0.10,
            "adjustment": 0.15  
        },
        BodyGoal.MAINTENANCE.name: {
            "breakfast": 0.30,
            "lunch": 0.35,
            "supper": 0.30,
            "snacks": 0.05,
            "adjustment": 0.0
        }
    }
    
    # Serving quantity ranges by body goal
    SERVING_RANGES = {
        BodyGoal.WEIGHT_LOSS.name: {
            "main_min": 1, "main_max": 2,
            "side_min": 1, "side_max": 1,
            "beverage_min": 1, "beverage_max": 1
        },
        BodyGoal.MUSCLE_GAIN.name: {
            "main_min": 2, "main_max": 4,
            "side_min": 1, "side_max": 2,
            "beverage_min": 1, "beverage_max": 2
        },
        BodyGoal.MAINTENANCE.name: {
            "main_min": 1, "main_max": 3,
            "side_min": 1, "side_max": 2,
            "beverage_min": 1, "beverage_max": 1
        }
    }
    
    @staticmethod
    async def filter_by_dietary_requirements(
        db: Session,
        dietary_restrictions: List[str],
        allergies: List[str],
        medical_conditions: List[str],
        food_list: List[FoodRead]
    ) -> List[FoodRead]:
        """
        Filter foods based on dietary preferences, allergies, and medical conditions.
        """
        
        if not (dietary_restrictions or allergies or medical_conditions):
            logger.info("No dietary requirements, returning all foods")
            return food_list
        
        logger.info(f"Filtering - Preferences: {dietary_restrictions}, Allergies: {allergies}, Conditions: {medical_conditions}")
        
        filtered_foods = []
        
        for food in food_list:
            include_food = True
            
            if dietary_restrictions:
                food_tags = getattr(food, 'dietary_tags', [])
                if not any(pref in food_tags for pref in dietary_restrictions):
                    include_food = False
                    continue
            
            if allergies:
                food_allergens = getattr(food, 'allergens', [])
                if any(allergen in food_allergens for allergen in allergies):
                    include_food = False
                    continue
                
            if medical_conditions:
                suitable_conditions = getattr(food, 'suitable_for_conditions', [])
                if not all(condition in suitable_conditions for condition in medical_conditions):
                    include_food = False
                    continue
            
            if include_food:
                filtered_foods.append(food)
        
        logger.info(f"Found {len(filtered_foods)} foods matching all requirements")
        return filtered_foods
    
    @staticmethod
    def _categorize_foods(food_list: List[FoodRead]) -> Dict[str, List[FoodRead]]:
        """Categorize foods by meal type for easier selection."""
        categories = {
            "breakfast": [],
            "lunch_supper": [],
            "fruits": [],
            "beverages": [],
            "side_dishes": []
        }
        
        for food in food_list:
            meal_type = food.meal_type.lower()
            
            if "breakfast" in meal_type or "snack" in meal_type:
                categories["breakfast"].append(food)
            if "lunch" in meal_type or "supper" in meal_type:
                categories["lunch_supper"].append(food)
            if "fruit" in meal_type:
                categories["fruits"].append(food)
            if "beverage" in meal_type:
                categories["beverages"].append(food)
            if "side" in meal_type:
                categories["side_dishes"].append(food)
        
        return categories
    
    @staticmethod
    def _select_food_with_priority(
        food_list: List[FoodRead], 
        body_goal: str, 
        prefer_high_calorie: bool = True
    ) -> FoodRead:
        """
        Select food based on body goal priorities.
        For muscle gain: prefer higher calorie foods
        For weight loss: prefer lower calorie foods
        For maintenance: balanced selection
        """
        if not food_list:
            return None
        
        if body_goal == BodyGoal.MUSCLE_GAIN.name and prefer_high_calorie:
            sorted_foods = sorted(food_list, key=lambda x: x.calories.total, reverse=True)
            top_30_percent = max(1, len(sorted_foods) // 3)
            return random.choice(sorted_foods[:top_30_percent])
        
        elif body_goal == BodyGoal.WEIGHT_LOSS.name and not prefer_high_calorie:
            sorted_foods = sorted(food_list, key=lambda x: x.calories.total)
            bottom_30_percent = max(1, len(sorted_foods) // 3)
            return random.choice(sorted_foods[:bottom_30_percent])
        
        else:  # Maintenance or balanced selection
            return random.choice(food_list)
    
    @staticmethod
    def _calculate_optimal_serving(
        food_calories: float,
        target_calories: float,
        min_serving: int,
        max_serving: int
    ) -> int:
        """
        Calculate optimal serving quantity to approach target calories.
        """
        if food_calories == 0:
            return min_serving
        
        # Calculate ideal serving
        ideal_serving = target_calories / food_calories
        
        # Clamp to min/max range
        optimal = round(ideal_serving)
        optimal = max(min_serving, min(optimal, max_serving))
        
        return optimal
    
    @staticmethod
    def _add_or_update_food(meal_items: List[SelectedFood], new_food: SelectedFood) -> float:
        """
        Add a new food to meal or update serving quantity if it already exists.
        Returns the calories added.
        """
        for existing_food in meal_items:
            if existing_food.id == new_food.id:
                # Food already exists, increase serving quantity
                existing_food.serving_quantity += new_food.serving_quantity
                return new_food.calories * new_food.serving_quantity
        
        # Food doesn't exist, add it
        meal_items.append(new_food)
        return new_food.calories * new_food.serving_quantity
    
    @staticmethod
    async def generate_user_meal_plan(
        db: Session, 
        food_list: List[FoodRead], 
        daily_calorie_target: int,
        body_goal: str
    ) -> List[Dict]:
        """
        Generate an intelligent meal plan with serving quantities based on body goals.
        """
        
        if body_goal not in MealPlanHelpers.CALORIE_DISTRIBUTION:
            logger.warning(f"Unknown body goal: {body_goal}, defaulting to MAINTENANCE")
            body_goal = BodyGoal.MAINTENANCE.name
        
        # Get calorie distribution and serving ranges for this body goal
        distribution = MealPlanHelpers.CALORIE_DISTRIBUTION[body_goal]
        serving_config = MealPlanHelpers.SERVING_RANGES[body_goal]
        
        # Adjust daily target based on body goal
        adjusted_target = daily_calorie_target * (1 + distribution["adjustment"])
        
        # Calculate target calories per meal
        breakfast_target = adjusted_target * distribution["breakfast"]
        lunch_target = adjusted_target * distribution["lunch"]
        supper_target = adjusted_target * distribution["supper"]
        
        logger.info(f"Body Goal: {body_goal}")
        logger.info(f"Daily Target: {daily_calorie_target} → Adjusted: {adjusted_target:.0f}")
        logger.info(f"Meal Targets - Breakfast: {breakfast_target:.0f}, Lunch: {lunch_target:.0f}, Supper: {supper_target:.0f}")
        
        # Categorize available foods
        categorized_foods = MealPlanHelpers._categorize_foods(food_list)
        
        # Verify we have foods in each category
        if not categorized_foods["breakfast"]:
            logger.warning("No breakfast foods available!")
        if not categorized_foods["lunch_supper"]:
            logger.warning("No lunch/supper foods available!")
        
        # Generate meal plan for each day
        days_of_the_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meal_plan = []
        
        for day_index, day in enumerate(days_of_the_week):
            day_plan = {
                "day": day,
                "meal_plan": {
                    "breakfast": [],
                    "lunch": [],
                    "supper": []
                },
                "total_calories": 0
            }
            
            # === BREAKFAST ===
            breakfast_calories = 0
            if categorized_foods["breakfast"]:
                # Select main breakfast item(s)
                num_main_items = random.randint(serving_config["main_min"], serving_config["main_max"])
                remaining_breakfast_target = breakfast_target
                
                for _ in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        categorized_foods["breakfast"],
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        # Calculate serving quantity
                        serving_qty = MealPlanHelpers._calculate_optimal_serving(
                            food.calories.total,
                            remaining_breakfast_target / num_main_items,
                            1,
                            4 if body_goal == BodyGoal.MUSCLE_GAIN.name else 2
                        )
                        
                        item_total_calories = food.calories.total * serving_qty
                        
                   
                        calories_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["breakfast"],
                            SelectedFood(
                                id=food.food_id,
                                name=food.name,
                                image_url=food.image_url,
                                calories=food.calories.total,
                                serving_quantity=serving_qty
                            )
                        )
                        
                        breakfast_calories += calories_added
                        remaining_breakfast_target -= calories_added
                
                # Add beverage
                if categorized_foods["beverages"] and random.random() > 0.2:  # 80% chance
                    beverage = random.choice(categorized_foods["beverages"])
                    serving_qty = random.randint(1, serving_config["beverage_max"])
                    
                    calories_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["breakfast"],
                        SelectedFood(
                            id=beverage.food_id,
                            name=beverage.name,
                            image_url=beverage.image_url,
                            calories=beverage.calories.total,
                            serving_quantity=serving_qty
                        )
                    )
                    breakfast_calories += calories_added
                
                # Add fruit if there's room
                if categorized_foods["fruits"] and breakfast_calories < breakfast_target * 0.9:
                    fruit = random.choice(categorized_foods["fruits"])
                    serving_qty = random.randint(1, 2)
                    
                    calories_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["breakfast"],
                        SelectedFood(
                            id=fruit.food_id,
                            name=fruit.name,
                            image_url=fruit.image_url,
                            calories=fruit.calories.total,
                            serving_quantity=serving_qty
                        )
                    )
                    breakfast_calories += calories_added
            
            # === LUNCH ===
            lunch_calories = 0
            if categorized_foods["lunch_supper"]:
                # Select main dish(es)
                num_main_items = random.randint(1, 2)
                remaining_lunch_target = lunch_target
                
                for _ in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        categorized_foods["lunch_supper"],
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        serving_qty = MealPlanHelpers._calculate_optimal_serving(
                            food.calories.total,
                            remaining_lunch_target / num_main_items,
                            1,
                            3 if body_goal == BodyGoal.MUSCLE_GAIN.name else 2
                        )
                        
                        item_total_calories = food.calories.total * serving_qty
                        
                        # Use helper to add or update existing food
                        calories_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["lunch"],
                            SelectedFood(
                                id=food.food_id,
                                name=food.name,
                                image_url=food.image_url,
                                calories=food.calories.total,
                                serving_quantity=serving_qty
                            )
                        )
                        
                        lunch_calories += calories_added
                        remaining_lunch_target -= calories_added
                
                # Add side dish or vegetable
                if categorized_foods["side_dishes"] and random.random() > 0.3:
                    side = random.choice(categorized_foods["side_dishes"])
                    serving_qty = random.randint(serving_config["side_min"], serving_config["side_max"])
                    
                    calories_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["lunch"],
                        SelectedFood(
                            id=side.food_id,
                            name=side.name,
                            image_url=side.image_url,
                            calories=side.calories.total,
                            serving_quantity=serving_qty
                        )
                    )
                    lunch_calories += calories_added
                
                # Add beverage
                if categorized_foods["beverages"] and random.random() > 0.4:
                    beverage = random.choice(categorized_foods["beverages"])
                    calories_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["lunch"],
                        SelectedFood(
                            id=beverage.food_id,
                            name=beverage.name,
                            image_url=beverage.image_url,
                            calories=beverage.calories.total,
                            serving_quantity=1
                        )
                    )
                    lunch_calories += calories_added
            
            # === SUPPER ===
            supper_calories = 0
            if categorized_foods["lunch_supper"]:
                # Select different main dish(es) from lunch
                lunch_food_ids = {item.id for item in day_plan["meal_plan"]["lunch"]}
                available_supper_foods = [
                    f for f in categorized_foods["lunch_supper"] 
                    if f.food_id not in lunch_food_ids
                ]
                
                if not available_supper_foods:
                    available_supper_foods = categorized_foods["lunch_supper"]
                
                num_main_items = random.randint(1, 2)
                remaining_supper_target = supper_target
                
                for _ in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        available_supper_foods,
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        serving_qty = MealPlanHelpers._calculate_optimal_serving(
                            food.calories.total,
                            remaining_supper_target / num_main_items,
                            1,
                            3 if body_goal == BodyGoal.MUSCLE_GAIN.name else 2
                        )
                        
                        item_total_calories = food.calories.total * serving_qty
                        
                        # Use helper to add or update existing food
                        calories_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["supper"],
                            SelectedFood(
                                id=food.food_id,
                                name=food.name,
                                image_url=food.image_url,
                                calories=food.calories.total,
                                serving_quantity=serving_qty
                            )
                        )
                        
                        supper_calories += calories_added
                        remaining_supper_target -= calories_added
                
                # Add side dish
                if categorized_foods["side_dishes"] and random.random() > 0.3:
                    side = random.choice(categorized_foods["side_dishes"])
                    serving_qty = random.randint(serving_config["side_min"], serving_config["side_max"])
                    
                    calories_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["supper"],
                        SelectedFood(
                            id=side.food_id,
                            name=side.name,
                            image_url=side.image_url,
                            calories=side.calories.total,
                            serving_quantity=serving_qty
                        )
                    )
                    supper_calories += calories_added
            
            # Calculate total calories for the day
            day_total = breakfast_calories + lunch_calories + supper_calories
            day_plan["total_calories"] = round(day_total)
            
            meal_plan.append(day_plan)
        
        # Calculate weekly totals
        weekly_total = sum(day["total_calories"] for day in meal_plan)
        avg_daily = weekly_total / 7
        
        logger.info(f"Generated meal plan - Weekly Total: {weekly_total:.0f}, Avg Daily: {avg_daily:.0f} (Target: {adjusted_target:.0f})")
        
        return meal_plan