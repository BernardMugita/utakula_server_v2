# controllers/helpers/serving_size_helper.py

class ServingSizeHelper:
    """
    Category-based default serving sizes in grams
    Used when calculating user-friendly serving counts
    """
    
    # Default serving sizes by macro nutrient category
    SERVING_SIZES_BY_MACRO = {
        "Protein": 150,      # e.g., chicken breast, fish, beef
        "Carbohydrate": 200, # e.g., rice, ugali, pasta
        "Fat": 15,           # e.g., oils, butter, nuts (smaller portions)
        "Fiber": 100,        # e.g., vegetables, salads
    }
    
    # Default serving sizes by meal type (overrides macro if specified)
    SERVING_SIZES_BY_MEAL_TYPE = {
        "beverage": 250,          # ml (1 cup)
        "fruit": 120,             # medium fruit
        "side dish": 100,         # side portion
        "breakfast or snack": 80, # breakfast item
        "lunch or supper": 150,   # main meal portion
    }
    
    @staticmethod
    def get_typical_serving_size(macro_nutrient: str, meal_type: str) -> int:
        """
        Get typical serving size for a food based on its category
        
        Args:
            macro_nutrient: Primary macronutrient (Protein, Carbohydrate, Fat, Fiber)
            meal_type: Meal type from MealTypeEnum
            
        Returns:
            Typical serving size in grams
        """
        # Check meal type first (more specific)
        if meal_type.lower() in ServingSizeHelper.SERVING_SIZES_BY_MEAL_TYPE:
            return ServingSizeHelper.SERVING_SIZES_BY_MEAL_TYPE[meal_type.lower()]
        
        # Fall back to macro nutrient category
        return ServingSizeHelper.SERVING_SIZES_BY_MACRO.get(macro_nutrient, 100)
    
    @staticmethod
    def calculate_servings(grams: float, macro_nutrient: str, meal_type: str) -> float:
        """
        Calculate number of servings based on grams
        
        Args:
            grams: Weight in grams
            macro_nutrient: Primary macronutrient
            meal_type: Meal type
            
        Returns:
            Number of servings (rounded to 1 decimal place)
        """
        typical_serving = ServingSizeHelper.get_typical_serving_size(macro_nutrient, meal_type)
        servings = grams / typical_serving
        return round(servings, 1)
    
    @staticmethod
    def calculate_grams_from_servings(servings: float, macro_nutrient: str, meal_type: str) -> float:
        """
        Calculate grams from number of servings
        
        Args:
            servings: Number of servings
            macro_nutrient: Primary macronutrient
            meal_type: Meal type
            
        Returns:
            Weight in grams
        """
        typical_serving = ServingSizeHelper.get_typical_serving_size(macro_nutrient, meal_type)
        return round(servings * typical_serving, 1)