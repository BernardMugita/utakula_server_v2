# controllers/helpers/tdee_calculator.py
import logging

logger = logging.getLogger(__name__)

class TDEECalculator:
    """
    Implements Katch-McArdle Formula for TDEE calculation
    Reference: https://tdeecalculator.net
    """
    
    # Activity level multipliers
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,           # Little to no exercise
        "lightly_active": 1.375,    # Light exercise 1-3 days/week
        "moderately_active": 1.55,  # Moderate exercise 3-5 days/week
        "very_active": 1.725,       # Hard exercise 6-7 days/week
        "extra_active": 1.9         # Very hard exercise & physical job or training twice per day
    }
    
    @staticmethod
    def calculate_lean_body_mass(weight_kg: float, body_fat_percentage: float) -> float:
        """
        Calculate lean body mass (LBM) in kg
        LBM = Total Weight × (1 - Body Fat Percentage/100)
        
        Args:
            weight_kg: Body weight in kilograms
            body_fat_percentage: Body fat as a percentage (e.g., 20.5 for 20.5%)
            
        Returns:
            Lean body mass in kg
        """
        lbm = weight_kg * (1 - body_fat_percentage / 100)
        logger.info(f"Calculated LBM: {lbm:.2f}kg from weight {weight_kg}kg and BF% {body_fat_percentage}%")
        return lbm
    
    @staticmethod
    def calculate_bmr_katch_mcardle(lean_body_mass_kg: float) -> float:
        """
        Katch-McArdle Formula for Basal Metabolic Rate (BMR)
        BMR = 370 + (21.6 × LBM in kg)
        
        This is the most accurate BMR formula when body fat percentage is known,
        as it accounts for lean body mass rather than just total weight.
        
        Args:
            lean_body_mass_kg: Lean body mass in kilograms
            
        Returns:
            BMR in kcal/day
        """
        bmr = 370 + (21.6 * lean_body_mass_kg)
        logger.info(f"Calculated BMR (Katch-McArdle): {bmr:.2f} kcal/day from LBM {lean_body_mass_kg:.2f}kg")
        return bmr
    
    @staticmethod
    def calculate_tdee(
        weight_kg: float,
        body_fat_percentage: float,
        activity_level: str
    ) -> float:
        """
        Calculate Total Daily Energy Expenditure (TDEE)
        TDEE = BMR × Activity Multiplier
        
        Args:
            weight_kg: Body weight in kilograms
            body_fat_percentage: Body fat as a percentage
            activity_level: Activity level key (sedentary, lightly_active, etc.)
            
        Returns:
            TDEE in kcal/day
        """
        # Calculate lean body mass
        lbm = TDEECalculator.calculate_lean_body_mass(weight_kg, body_fat_percentage)
        
        # Calculate BMR using Katch-McArdle
        bmr = TDEECalculator.calculate_bmr_katch_mcardle(lbm)
        
        # Apply activity multiplier
        multiplier = TDEECalculator.ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
        tdee = bmr * multiplier
        
        logger.info(f"Calculated TDEE: {tdee:.2f} kcal/day (BMR: {bmr:.2f}, Activity: {activity_level}, Multiplier: {multiplier})")
        return round(tdee, 2)
    
    @staticmethod
    def adjust_for_body_goal(tdee: float, body_goal: str) -> float:
        """
        Adjust TDEE based on body goal
        
        Adjustments:
        - WEIGHT_LOSS: -500 kcal (approximately 0.5kg loss per week)
        - MUSCLE_GAIN: +400 kcal (lean bulking surplus)
        - MAINTENANCE: no change
        
        Args:
            tdee: Base TDEE in kcal/day
            body_goal: Body goal (WEIGHT_LOSS, MUSCLE_GAIN, MAINTENANCE)
            
        Returns:
            Adjusted calorie target in kcal/day
        """
        adjustments = {
            "WEIGHT_LOSS": -500,
            "MUSCLE_GAIN": 400,
            "MAINTENANCE": 0
        }
        
        adjustment = adjustments.get(body_goal, 0)
        adjusted_calories = tdee + adjustment
        
        logger.info(f"Adjusted TDEE for {body_goal}: {adjusted_calories:.2f} kcal/day (TDEE: {tdee:.2f}, Adjustment: {adjustment:+d})")
        
        return round(adjusted_calories, 2)