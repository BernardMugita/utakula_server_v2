# controllers/helpers/meal_plan_helpers.py
import logging
import random
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from models.food_model import FoodModel
from schemas.calorie_schema import FoodRead
from schemas.meal_plan_schema import SelectedFood, MacroBreakdown
from utils.enums import BodyGoal
from controllers.helpers.service_size_helper import ServingSizeHelper

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
        },
        BodyGoal.MUSCLE_GAIN.name: {
            "breakfast": 0.25,
            "lunch": 0.35,
            "supper": 0.30,
            "snacks": 0.10,
        },
        BodyGoal.MAINTENANCE.name: {
            "breakfast": 0.30,
            "lunch": 0.35,
            "supper": 0.30,
            "snacks": 0.05,
        }
    }
    
    # Grams ranges by body goal (for main items)
    GRAMS_RANGES = {
        BodyGoal.WEIGHT_LOSS.name: {
            "main_min_grams": 100, 
            "main_max_grams": 200,
            "side_min_grams": 80,
            "side_max_grams": 100,
        },
        BodyGoal.MUSCLE_GAIN.name: {
            "main_min_grams": 200,
            "main_max_grams": 400,
            "side_min_grams": 100,
            "side_max_grams": 200,
        },
        BodyGoal.MAINTENANCE.name: {
            "main_min_grams": 150,
            "main_max_grams": 300,
            "side_min_grams": 80,
            "side_max_grams": 150,
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
    def _calculate_grams_for_calories(
        calories_per_100g: float,
        target_calories: float,
        min_grams: float,
        max_grams: float
    ) -> float:
        """
        Calculate grams needed to hit target calories, bounded by min/max
        
        Formula: grams = (target_calories / calories_per_100g) * 100
        """
        if calories_per_100g == 0:
            return min_grams
        
        # Calculate ideal grams
        ideal_grams = (target_calories / calories_per_100g) * 100
        
        # Clamp to min/max range
        optimal_grams = max(min_grams, min(ideal_grams, max_grams))
        
        return round(optimal_grams, 1)
    
    @staticmethod
    def _calculate_macros_for_portion(
        food: FoodRead,
        grams: float,
        reference_portion_grams: int = 100
    ) -> MacroBreakdown:
        """
        Calculate macro breakdown for a specific portion size
        
        Args:
            food: FoodRead object with calorie breakdown
            grams: Portion size in grams
            reference_portion_grams: Reference portion (usually 100g)
            
        Returns:
            MacroBreakdown with calculated values
        """
        
        multiplier = grams / reference_portion_grams
        
        breakdown = food.calories.breakdown
        
        return MacroBreakdown(
            protein_g=round(breakdown.protein.amount * multiplier, 1),
            carbs_g=round(breakdown.carbohydrate.amount * multiplier, 1),
            fat_g=round(breakdown.fat.amount * multiplier, 1),
            fiber_g=round(breakdown.fiber.amount * multiplier, 1)
        )
    
    @staticmethod
    def _create_selected_food(
        food: FoodRead,
        grams: float,
        reference_portion_grams: int = 100
    ) -> SelectedFood:
        """
        Create a SelectedFood object with calculated calories, servings, and macros
        """
        # Calculate total calories for this portion
        calories_per_100g = food.calories.total
        total_calories = (grams / reference_portion_grams) * calories_per_100g
        
        # Calculate servings (human-friendly display)
        servings = ServingSizeHelper.calculate_servings(
            grams, 
            food.macro_nutrient, 
            food.meal_type
        )
        
        # Calculate macro breakdown
        macros = MealPlanHelpers._calculate_macros_for_portion(
            food, 
            grams, 
            reference_portion_grams
        )
        
        print(macros)
        
        return SelectedFood(
            id=food.food_id,
            name=food.name,
            image_url=food.image_url,
            grams=grams,
            servings=servings,
            calories_per_100g=calories_per_100g,
            total_calories=round(total_calories, 1),
            macros=macros
        )
    
    @staticmethod
    def _add_or_update_food(
        meal_items: List[SelectedFood], 
        new_food: SelectedFood
    ) -> Tuple[float, MacroBreakdown]:
        """
        Add a new food to meal or update grams if it already exists.
        Returns the calories added and macros added.
        """
        for existing_food in meal_items:
            if existing_food.id == new_food.id:
                # Food already exists, increase grams
                existing_food.grams += new_food.grams
                existing_food.servings += new_food.servings
                existing_food.total_calories += new_food.total_calories
                
                # Update macros
                existing_food.macros.protein_g += new_food.macros.protein_g
                existing_food.macros.carbs_g += new_food.macros.carbs_g
                existing_food.macros.fat_g += new_food.macros.fat_g
                existing_food.macros.fiber_g += new_food.macros.fiber_g
                
                return new_food.total_calories, new_food.macros
        
        # Food doesn't exist, add it
        meal_items.append(new_food)
        return new_food.total_calories, new_food.macros
    
    @staticmethod
    async def generate_user_meal_plan(
        db: Session, 
        food_list: List[FoodRead], 
        daily_calorie_target: float,
        body_goal: str
    ) -> List[Dict]:
        """
        Generate an intelligent meal plan with grams-based portions
        """
        
        if body_goal not in MealPlanHelpers.CALORIE_DISTRIBUTION:
            logger.warning(f"Unknown body goal: {body_goal}, defaulting to MAINTENANCE")
            body_goal = BodyGoal.MAINTENANCE.name
        
        # Get calorie distribution and grams ranges for this body goal
        distribution = MealPlanHelpers.CALORIE_DISTRIBUTION[body_goal]
        grams_config = MealPlanHelpers.GRAMS_RANGES[body_goal]
        
        # Calculate target calories per meal
        breakfast_target = daily_calorie_target * distribution["breakfast"]
        lunch_target = daily_calorie_target * distribution["lunch"]
        supper_target = daily_calorie_target * distribution["supper"]
        
        logger.info(f"Body Goal: {body_goal}")
        logger.info(f"Daily Target: {daily_calorie_target:.0f} kcal")
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
                "total_calories": 0,
                "total_macros": MacroBreakdown(protein_g=0, carbs_g=0, fat_g=0, fiber_g=0)
            }
            
            # === BREAKFAST ===
            breakfast_calories = 0
            breakfast_macros = MacroBreakdown(protein_g=0, carbs_g=0, fat_g=0, fiber_g=0)
            
            if categorized_foods["breakfast"]:
                # Select 1-2 main breakfast items
                num_main_items = random.randint(1, 2)
                remaining_breakfast_target = breakfast_target
                
                for i in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        categorized_foods["breakfast"],
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        # Calculate grams needed for portion of target
                        target_for_this_item = remaining_breakfast_target / (num_main_items - i)
                        grams = MealPlanHelpers._calculate_grams_for_calories(
                            food.calories.total,
                            target_for_this_item,
                            grams_config["main_min_grams"],
                            grams_config["main_max_grams"]
                        )
                        
                        selected_food = MealPlanHelpers._create_selected_food(food, grams)
                        
                        calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["breakfast"],
                            selected_food
                        )
                        
                        breakfast_calories += calories_added
                        breakfast_macros.protein_g += macros_added.protein_g
                        breakfast_macros.carbs_g += macros_added.carbs_g
                        breakfast_macros.fat_g += macros_added.fat_g
                        breakfast_macros.fiber_g += macros_added.fiber_g
                        remaining_breakfast_target -= calories_added
                
                # Add beverage (80% chance)
                if categorized_foods["beverages"] and random.random() > 0.2:
                    beverage = random.choice(categorized_foods["beverages"])
                    grams = random.randint(200, 300)  # 200-300ml
                    
                    selected_food = MealPlanHelpers._create_selected_food(beverage, grams)
                    calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["breakfast"],
                        selected_food
                    )
                    breakfast_calories += calories_added
                    breakfast_macros.protein_g += macros_added.protein_g
                    breakfast_macros.carbs_g += macros_added.carbs_g
                    breakfast_macros.fat_g += macros_added.fat_g
                    breakfast_macros.fiber_g += macros_added.fiber_g
                
                # Add fruit if there's room
                if categorized_foods["fruits"] and breakfast_calories < breakfast_target * 0.9:
                    fruit = random.choice(categorized_foods["fruits"])
                    grams = random.randint(100, 150)  # 100-150g
                    
                    selected_food = MealPlanHelpers._create_selected_food(fruit, grams)
                    calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["breakfast"],
                        selected_food
                    )
                    breakfast_calories += calories_added
                    breakfast_macros.protein_g += macros_added.protein_g
                    breakfast_macros.carbs_g += macros_added.carbs_g
                    breakfast_macros.fat_g += macros_added.fat_g
                    breakfast_macros.fiber_g += macros_added.fiber_g
            
            # === LUNCH ===
            lunch_calories = 0
            lunch_macros = MacroBreakdown(protein_g=0, carbs_g=0, fat_g=0, fiber_g=0)
            
            if categorized_foods["lunch_supper"]:
                # Select 1-2 main dishes
                num_main_items = random.randint(1, 2)
                remaining_lunch_target = lunch_target
                
                for i in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        categorized_foods["lunch_supper"],
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        target_for_this_item = remaining_lunch_target / (num_main_items - i)
                        grams = MealPlanHelpers._calculate_grams_for_calories(
                            food.calories.total,
                            target_for_this_item,
                            grams_config["main_min_grams"],
                            grams_config["main_max_grams"]
                        )
                        
                        selected_food = MealPlanHelpers._create_selected_food(food, grams)
                        calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["lunch"],
                            selected_food
                        )
                        
                        lunch_calories += calories_added
                        lunch_macros.protein_g += macros_added.protein_g
                        lunch_macros.carbs_g += macros_added.carbs_g
                        lunch_macros.fat_g += macros_added.fat_g
                        lunch_macros.fiber_g += macros_added.fiber_g
                        remaining_lunch_target -= calories_added
                
                # Add side dish (70% chance)
                if categorized_foods["side_dishes"] and random.random() > 0.3:
                    side = random.choice(categorized_foods["side_dishes"])
                    grams = random.randint(
                        grams_config["side_min_grams"], 
                        grams_config["side_max_grams"]
                    )
                    
                    selected_food = MealPlanHelpers._create_selected_food(side, grams)
                    calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["lunch"],
                        selected_food
                    )
                    lunch_calories += calories_added
                    lunch_macros.protein_g += macros_added.protein_g
                    lunch_macros.carbs_g += macros_added.carbs_g
                    lunch_macros.fat_g += macros_added.fat_g
                    lunch_macros.fiber_g += macros_added.fiber_g
                
                # Add beverage (60% chance)
                if categorized_foods["beverages"] and random.random() > 0.4:
                    beverage = random.choice(categorized_foods["beverages"])
                    grams = 250  # 250ml standard
                    
                    selected_food = MealPlanHelpers._create_selected_food(beverage, grams)
                    calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["lunch"],
                        selected_food
                    )
                    lunch_calories += calories_added
                    lunch_macros.protein_g += macros_added.protein_g
                    lunch_macros.carbs_g += macros_added.carbs_g
                    lunch_macros.fat_g += macros_added.fat_g
                    lunch_macros.fiber_g += macros_added.fiber_g
            
            # === SUPPER ===
            supper_calories = 0
            supper_macros = MacroBreakdown(protein_g=0, carbs_g=0, fat_g=0, fiber_g=0)
            
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
                
                for i in range(num_main_items):
                    food = MealPlanHelpers._select_food_with_priority(
                        available_supper_foods,
                        body_goal,
                        prefer_high_calorie=(body_goal == BodyGoal.MUSCLE_GAIN.name)
                    )
                    
                    if food:
                        target_for_this_item = remaining_supper_target / (num_main_items - i)
                        grams = MealPlanHelpers._calculate_grams_for_calories(
                            food.calories.total,
                            target_for_this_item,
                            grams_config["main_min_grams"],
                            grams_config["main_max_grams"]
                        )
                        
                        selected_food = MealPlanHelpers._create_selected_food(food, grams)
                        calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                            day_plan["meal_plan"]["supper"],
                            selected_food
                        )
                        
                        supper_calories += calories_added
                        supper_macros.protein_g += macros_added.protein_g
                        supper_macros.carbs_g += macros_added.carbs_g
                        supper_macros.fat_g += macros_added.fat_g
                        supper_macros.fiber_g += macros_added.fiber_g
                        remaining_supper_target -= calories_added
                
                # Add side dish (70% chance)
                if categorized_foods["side_dishes"] and random.random() > 0.3:
                    side = random.choice(categorized_foods["side_dishes"])
                    grams = random.randint(
                        grams_config["side_min_grams"], 
                        grams_config["side_max_grams"]
                    )
                    
                    selected_food = MealPlanHelpers._create_selected_food(side, grams)
                    calories_added, macros_added = MealPlanHelpers._add_or_update_food(
                        day_plan["meal_plan"]["supper"],
                        selected_food
                    )
                    supper_calories += calories_added
                    supper_macros.protein_g += macros_added.protein_g
                    supper_macros.carbs_g += macros_added.carbs_g
                    supper_macros.fat_g += macros_added.fat_g
                    supper_macros.fiber_g += macros_added.fiber_g
            
            # Calculate day totals
            day_total = breakfast_calories + lunch_calories + supper_calories
            day_plan["total_calories"] = round(day_total, 1)
            
            # Sum up macros
            day_plan["total_macros"] = MacroBreakdown(
                protein_g=round(breakfast_macros.protein_g + lunch_macros.protein_g + supper_macros.protein_g, 1),
                carbs_g=round(breakfast_macros.carbs_g + lunch_macros.carbs_g + supper_macros.carbs_g, 1),
                fat_g=round(breakfast_macros.fat_g + lunch_macros.fat_g + supper_macros.fat_g, 1),
                fiber_g=round(breakfast_macros.fiber_g + lunch_macros.fiber_g + supper_macros.fiber_g, 1)
            )
            
            meal_plan.append(day_plan)
        
        # Calculate weekly totals
        weekly_total = sum(day["total_calories"] for day in meal_plan)
        avg_daily = weekly_total / 7
        
        logger.info(f"Generated meal plan - Weekly Total: {weekly_total:.0f}, Avg Daily: {avg_daily:.0f} (Target: {daily_calorie_target:.0f})")
        
        return meal_plan