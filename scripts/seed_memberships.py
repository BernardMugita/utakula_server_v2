"""
Run this script once to create the initial PLUS and ELITE membership tiers.
Usage: python scripts/seed_memberships.py
"""

from sqlalchemy.orm import Session
from connect import SessionLocal
from models.membership_model import MembershipModel
from utils.enums import MembershipType, BillingCycle

def seed_memberships():
    db: Session = SessionLocal()
    
    try:
        # Check if memberships already exist
        existing = db.query(MembershipModel).first()
        if existing:
            print("Memberships already exist. Skipping seed.")
            return
        
        # Create PLUS membership
        plus_membership = MembershipModel(
            membership_type=MembershipType.PLUS,
            membership_name="Utakula Plus",
            membership_description="Perfect for individuals who want to plan meals and track nutrition",
            membership_price=600.00,  # KES 399/month (adjust as needed)
            billing_cycle=BillingCycle.MONTHLY,
            features={
                "unlimited_meal_planning": True,
                "wearable_sync": True,
                "shared_meal_plans": True,
                "max_shared_users": 3,
                "custom_templates": 3,
                "shuffle_mealplans": True,
                "max_shuffles": 3,
                "cultural_cuisines": ["Kenyan", "Ethiopian", "Ugandan"],
                "no_ads": True,
                "priority_support": False
            },
            is_active=True
        )
        
        # Create ELITE membership
        elite_membership = MembershipModel(
            membership_type=MembershipType.ELITE,
            membership_name="Utakula Elite",
            membership_description="For families and fitness enthusiasts who want premium features",
            membership_price=800.00,
            billing_cycle=BillingCycle.MONTHLY,
            features={
                "unlimited_meal_planning": True,
                "wearable_sync": True,
                "shared_meal_plans": True,
                "max_shared_users": 5,
                "custom_templates": "all",
                "shuffle_mealplans": True,
                "max_shuffles": 3,
                "cultural_cuisines": ["all_expanding_monthly"],
                "no_ads": True,
                "priority_support": True,
                "macro_tracking": True,
                "progress_photos": True,
                "early_access": True,
                "recipe_export": True
            },
            is_active=True
        )
        
        db.add(plus_membership)
        db.add(elite_membership)
        db.commit()
        
        print("✅ Memberships seeded successfully!")
        print(f"   - {plus_membership.membership_name}: KES {plus_membership.membership_price}/month")
        print(f"   - {elite_membership.membership_name}: KES {elite_membership.membership_price}/month")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding memberships: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_memberships()