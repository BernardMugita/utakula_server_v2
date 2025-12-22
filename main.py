from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from routes.food_routes import router as food_router
from routes.calorie_routes import router as calorie_router
from routes.meal_plan_routes import router as meal_plan_router
from routes.invitation_routes import router as invitation_router
from routes.genai_routes import router as genai_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Where is the food"}

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(food_router)
app.include_router(calorie_router)
app.include_router(meal_plan_router)
app.include_router(invitation_router)
app.include_router(genai_router)

