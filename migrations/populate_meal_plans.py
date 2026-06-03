import uuid
from fastapi.params import Depends
from sqlalchemy.orm import Session
from connect import SessionLocal
from models.meal_plan_model import MealPlanModel
from models.meal_plan_day_model import MealPlanDayModel
from models.meal_plan_meal_model import MealPlanMealModel
from models.meal_plan_food_item_model import MealPlanFoodItemModel
    


def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def populate_meal_plans(db: Session = Depends(get_db_connection)):
    meal_plans = db.query(MealPlanModel).all()

    total = len(meal_plans)
    success_count = 0
    skipped_count = 0
    error_count = 0
    errors = []

    print(f"Found {total} meal plans to migrate.\n")

    for plan in meal_plans:
        try:
            # Skip if already normalized (day_plans already populated)
            if plan.day_plans:
                print(f"⏭️  Skipping meal plan {plan.id} (user: {plan.user_id}) — already normalized.")
                skipped_count += 1
                continue

            raw_days = plan.meal_plan  # The JSON blob — list of day objects

            if not raw_days:
                print(f"⚠️  Skipping meal plan {plan.id} — empty meal_plan JSON.")
                skipped_count += 1
                continue

            for day_data in raw_days:
                day_plan = MealPlanDayModel(
                    id=str(uuid.uuid4()),
                    meal_plan_id=plan.id,
                    day=day_data["day"],
                    total_calories=day_data.get("total_calories", 0.0)
                )
                db.add(day_plan)
                db.flush()  # Persist so day_plan.id is available

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
                    db.flush()  # Persist so meal.id is available

                    for food in food_list:
                        food_item = MealPlanFoodItemModel(
                            id=str(uuid.uuid4()),
                            meal_id=meal.id,
                            food_id=food["id"],  # Same as foods.food_id ✅
                            grams=food.get("grams", 0.0),
                            servings=food.get("servings", 1.0)
                        )
                        db.add(food_item)

            db.commit()
            success_count += 1
            print(f"✅ Migrated meal plan {plan.id} (user: {plan.user_id})")

        except Exception as e:
            db.rollback()
            error_count += 1
            errors.append({"meal_plan_id": plan.id, "user_id": str(plan.user_id), "error": str(e)})
            print(f"❌ Failed meal plan {plan.id} (user: {plan.user_id}): {e}")

    print(f"\n--- Migration Complete ---")
    print(f"Total:    {total}")
    print(f"✅ Success:  {success_count}")
    print(f"⏭️  Skipped:  {skipped_count}")
    print(f"❌ Failed:   {error_count}")

    if errors:
        print("\nFailed plans:")
        for err in errors:
            print(f"  - meal_plan_id: {err['meal_plan_id']} | user_id: {err['user_id']} | error: {err['error']}")


if __name__ == "__main__":
    db = next(get_db_connection())
    try:
        populate_meal_plans(db)
    finally:
        db.close()