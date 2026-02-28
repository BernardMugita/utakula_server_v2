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

class MembershipType(str, Enum):
    PLUS = "plus"
    ELITE = "elite"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"  # 14-day free trial
    ACTIVE = "active"  # Paid and active
    GRACE_PERIOD = "grace_period"  # 7 days after payment failure
    EXPIRED = "expired"  # Hard cutoff after grace period
    CANCELLED = "cancelled"  # User cancelled but still has access until end date

class PaymentMethod(str, Enum):
    MPESA = "mpesa"
    STRIPE = "stripe"
    OTHER = "other"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"