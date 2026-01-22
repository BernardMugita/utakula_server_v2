from typing import List
from fastapi import Body, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from controllers.calorie_controller import CalorieController
from models.calorie_model import CalorieModel
from models.food_model import FoodModel
from schemas.calorie_schema import CalorieRead, FoodWithCaloriesCreate
from schemas.food_schema import CreateFoodResponse, DeleteFoodResponse, FoodCreate, FoodDelete, FoodGet, FoodRead, FoodUpdate, RetrieveFoodResponse, UpdateFoodResponse
from utils.helper_utils import HelperUtils

utils = HelperUtils()
calorie_controller = CalorieController()

class FoodController:
    def __init__(self) -> None:
        pass
    
    def add_new_food(self, food: FoodCreate, db: Session, authorization: str = Header(...)):
        """_summary_

        Args:
            food (FoodCreate): _description_
            db (Session): _description_
            authorization (str, optional): _description_. Defaults to Header(...).
        """
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:] 
            payload = utils.validate_JWT(token)  
            
            if payload['role'] != "admin":
                JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=CreateFoodResponse(
                    status="error",
                    message="Failed to add food",
                    payload=f"You are not authorized to access this route"
                ).dict()
            )
            
            existing_food = db.query(FoodModel).filter(
                FoodModel.name == food.name
            ).first()
            
            if existing_food:
                JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=CreateFoodResponse(
                    status="error",
                    message="Failed to add food",
                    payload=f"Food already exists"
                ).dict()
            )
                
            new_food = FoodModel(
                name=food.name,
                image_url=food.image_url,
                macro_nutrient=food.macro_nutrient,
                meal_type = food.meal_type
            )
            
            db.add(new_food)
            db.commit()
            db.refresh(new_food)
            
            return {
                "status": "success",
                "message": "Food added.",
                "payload": new_food
            }
          
        except Exception as e:
          return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateFoodResponse(
                    status="error",
                    message="Error when adding food!",
                    payload=f"{str(e)}"
                ).dict()
            )

    def add_bulk_food_with_calories(
        self, 
        foods_data: List[FoodCreate],
        db: Session, 
        authorization: str = Header(...)
    ):
        """
        Add multiple food items and their calorie data in a single transaction.
        """
        try:
            # Authorization validation
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:] 
            payload = utils.validate_JWT(token)  
            
            if payload['role'] != "admin":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=CreateFoodResponse(
                        status="error",
                        message="Failed to add food",
                        payload="You are not authorized to access this route"
                    ).dict()
                )
            
            added_foods = []
            skipped_foods = []
            
            for food_data in foods_data:
                # Check if food already exists
                existing_food = db.query(FoodModel).filter(
                    FoodModel.name == food_data.name
                ).first()
                
                if existing_food:
                    skipped_foods.append(food_data.name)
                    continue
                
                dietary_tags_list = []
                if food_data.dietary_tags:
                    dietary_tags_list = [
                        tag.value if hasattr(tag, 'value') else str(tag) 
                        for tag in food_data.dietary_tags
                    ]
                
                allergens_list = []
                if food_data.allergens:
                    allergens_list = [
                        allergen.value if hasattr(allergen, 'value') else str(allergen) 
                        for allergen in food_data.allergens
                    ]
                
                conditions_list = []
                if food_data.suitable_for_conditions:
                    conditions_list = [
                        condition.value if hasattr(condition, 'value') else str(condition) 
                        for condition in food_data.suitable_for_conditions
                    ]
                
                # Create new food
                new_food = FoodModel(
                    name=food_data.name,
                    image_url=food_data.image_url,
                    macro_nutrient=food_data.macro_nutrient,
                    meal_type=food_data.meal_type,
                    dietary_tags=dietary_tags_list,
                    allergens=allergens_list,
                    suitable_for_conditions=conditions_list
                )
                
                db.add(new_food)
                db.flush()  # Get the food_id without committing
                
                # Add calorie data
                calorie = CalorieModel(
                    food_id=new_food.id,
                    total=food_data.calories.total,
                    breakdown=food_data.calories.breakdown.dict()
                )
                
                db.add(calorie)
                
                # Prepare response for this food
                food_response = FoodRead(
                    food_id=str(new_food.id),
                    name=new_food.name,
                    image_url=new_food.image_url,
                    macro_nutrient=new_food.macro_nutrient,
                    meal_type=new_food.meal_type.value if hasattr(new_food.meal_type, 'value') else new_food.meal_type,
                    dietary_tags=dietary_tags_list,
                    allergens=allergens_list,
                    suitable_for_conditions=conditions_list,
                    calories=CalorieRead(
                        calorie_id=str(calorie.id),
                        food_id=str(new_food.id),
                        total=calorie.total,
                        breakdown=food_data.calories.breakdown
                    )
                )
                added_foods.append(food_response)

            db.commit()  # Commit all changes at once
            
            response_message = f"Successfully added {len(added_foods)} food items."
            if skipped_foods:
                response_message += f" Skipped {len(skipped_foods)} existing foods: {', '.join(skipped_foods[:5])}"
                if len(skipped_foods) > 5:
                    response_message += f" and {len(skipped_foods) - 5} more."
            
            return CreateFoodResponse(
                status="success",
                message=response_message,
                payload=added_foods
            )
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            print(f"Error in bulk add: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateFoodResponse(
                    status="error",
                    message="Failed to add food in bulk",
                    payload=str(e)
                ).dict()
            )
    
          
    def get_all_foods(self, db: Session, authorization: str = Header(...)):
        """Retrieve all foods along with their calorie breakdown.

        Args:
            db (Session): Database session.
            authorization (str, optional): Authorization header.

        Raises:
            HTTPException: If authorization fails.

        Returns:
            dict: A dictionary containing the status, message, and list of foods with calorie breakdown.
        """
        try:
            # Verify authorization
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )

            token = authorization[7:]
            utils.validate_JWT(token)

            # Retrieve all foods
            foods = db.query(FoodModel).all()
            
            # Create a list to store foods with calorie breakdown
            food_list = []
            
            for food in foods:
                # Retrieve calorie data for each food
                food_calories = db.query(CalorieModel).filter(CalorieModel.food_id == str(food.id)).first()
                
                # Create calorie breakdown data if available
                calorie_data = None
                if food_calories:
                    calorie_data = CalorieRead(
                        calorie_id=str(food_calories.id),  # Changed from id= to calorie_id=
                        food_id=str(food_calories.food_id),
                        total=food_calories.total,
                        breakdown=food_calories.breakdown
                    )

                # Append each food with calorie data to the food list
                food_list.append(FoodRead(
                    food_id=food.id,  # Changed from id= to food_id=
                    image_url=food.image_url,
                    name=food.name,
                    reference_portion_grams=food.reference_portion_grams,
                    macro_nutrient=food.macro_nutrient,
                    meal_type=food.meal_type,
                    calories=calorie_data,  # Changed from calorie_breakdown= to calories=
                    allergens=food.allergens,
                    dietary_tags=food.dietary_tags,
                    suitable_for_conditions=food.suitable_for_conditions
                ))

            return {
                "status": "success",
                "message": "List of all foods",
                "payload": food_list
            }
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveFoodResponse(
                    status="error",
                    message="Error when retrieving foods",
                    payload=str(e)
                ).dict()
            )


    def get_food_by_id(self, db: Session, food_data: FoodGet = Body(...), authorization: str = Header(...)):
        """Get a single food by ID with its calorie breakdown.

        Args:
            db (Session): Database session.
            food_data (FoodGet): Food ID to retrieve.
            authorization (str, optional): Authorization header.

        Raises:
            HTTPException: If authorization fails or food not found.

        Returns:
            dict: Food details with calorie breakdown.
        """
        
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:] 
            utils.validate_JWT(token)  

            # If token is valid, proceed to get the food by ID
            single_food = db.query(FoodModel).filter(FoodModel.id == str(food_data.id)).first()
            
            if not single_food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="food not found"
                )
                
            food_calories = db.query(CalorieModel).filter(CalorieModel.food_id == str(single_food.id)).first()
            
            print(food_calories)
            
            # Create calorie data if available
            calorie_data = None
            if food_calories:
                calorie_data = CalorieRead(
                    calorie_id=str(food_calories.id),  # Changed from id= to calorie_id=
                    food_id=str(food_calories.food_id),
                    total=food_calories.total,
                    breakdown=food_calories.breakdown
                )
            
            food = FoodRead(
                food_id=single_food.id,  # Changed from id= to food_id=
                image_url=single_food.image_url,
                name=single_food.name,
                macro_nutrient=single_food.macro_nutrient,
                meal_type=single_food.meal_type,
                calories=calorie_data  # Changed from calorie_breakdown= to calories=
            )
                
            return {
                "status": "success",
                "message": "Food details.",
                "payload": food
            }  
        except Exception as e:
            return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=RetrieveFoodResponse(
                        status="error",
                        message="Error when fetching food",
                        payload=f"{str(e)}",
                    ).dict()
                )
           
           
    def edit_food_details(self, db: Session, authorization: str = Header(...), food_data: FoodUpdate = Body(...)):
        """Edit the food's details.

        Args:
            db (Session): Database session.
            authorization (str): Authorization header.
            food_data (FoodUpdate): Data to update in the food.
        """
        
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:] 
            utils.validate_JWT(token)

            # Get the food by ID from the validated JWT payload
            food = db.query(FoodModel).filter(FoodModel.id == str(food_data.id)).first()
            if not food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="food not found"
                )
            
            if food_data.image_url is not None:
                food.image_url = food_data.image_url
            if food_data.name is not None:
                food.name = food_data.name
            if food_data.macro_nutrient is not None:
                food.macro_nutrient = food_data.macro_nutrient
            if food_data.meal_type is not None:
                food.meal_type = food_data.meal_type

            # Commit the changes to the database
            db.commit()
            db.refresh(food)  # Refresh the instance to get updated data

            # Return a response indicating success
            return {
                "status": "success",
                "message": "food details updated successfully",
                "payload": food
            }

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=UpdateFoodResponse(
                    status="error",
                    message="Error editing food",
                    payload=str(e)
                ).dict()
            )
            
            
    def delete_food_details(self, db: Session, food_data: FoodDelete = Body(...), authorization: str = Header(...)):
        """Delete the food's food.

        Args:
            db (Session): Database session.
            authorization (str): Authorization header.
        """
        
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:] 
            utils.validate_JWT(token)  

            food = db.query(FoodModel).filter(FoodModel.id == str(food_data.id)).first()
            if not food:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="food not found"
                )
            
            db.delete(food)
            db.commit() 
            
            return {
                "status": "success",
                "payload": "food deleted successfully",
            }

        except Exception as e:
            db.rollback() 
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=DeleteFoodResponse(
                    status="error",
                    payload=f"Error deleting food: {str(e)}",
                ).dict()
            )
    