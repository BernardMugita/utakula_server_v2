from enum import Enum

class BodyGoal(str, Enum):
    WEIGHT_LOSS = "Weight Loss"
    MUSCLE_GAIN = "Muscle Gain"
    MAINTENANCE = "Maintenance"
    
class DietaryRestriction(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    PESCATARIAN = "pescatarian"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    HALAL = "halal"
    KOSHER = "kosher"
    KETO = "keto"
    PALEO = "paleo"
    
class FoodAllergy(str, Enum):
    """Common food allergies"""
    GLUTEN = "gluten"
    DAIRY = "dairy"
    EGGS = "eggs"
    PEANUTS = "peanuts"
    TREE_NUTS = "tree_nuts"  # Almonds, walnuts, cashews, etc.
    SOY = "soy"
    SHELLFISH = "shellfish"
    FISH = "fish"
    SESAME = "sesame"
    WHEAT = "wheat"

class MedicalDietaryCondition(str, Enum):
    """Medical conditions requiring dietary modifications"""
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"  # High blood pressure
    HIGH_CHOLESTEROL = "high_cholesterol"
    CELIAC_DISEASE = "celiac_disease"  # Autoimmune gluten intolerance
    LACTOSE_INTOLERANCE = "lactose_intolerance"
    IBS = "ibs"  # Irritable Bowel Syndrome
    GERD = "gerd"  # Acid reflux
    KIDNEY_DISEASE = "kidney_disease"
    HEART_DISEASE = "heart_disease"
    GOUT = "gout"