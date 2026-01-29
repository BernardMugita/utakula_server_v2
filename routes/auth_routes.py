# user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user_model import UserModel
from schemas.user_schema import AuthResponse, OTPRequest, ResetPasswordRequest, ResetPasswordRequest, UserAuthorize, UserCreate, RegisterResponse
from connect import SessionLocal
from controllers.auth_controller import AuthController  # Import the controller

router = APIRouter()
auth_controller = AuthController()  # Create a controller instance

# Dependency to get the SQLAlchemy session
def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/auth/create_account/", response_model=RegisterResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db_connection)):
    try:
        return auth_controller.create_user_account(user, db)
    except HTTPException as e:
        raise e 

@router.post("/auth/authorize_account", response_model=AuthResponse)
async def authorize_user_account(user: UserAuthorize, db: Session = Depends(get_db_connection)):
    try:
        return auth_controller.authorize_user_account(user, db)
    except HTTPException as e:
        return e
    
@router.post("/auth/generate_otp", response_model=AuthResponse)
async def generate_otp_for_password_reset(otp_data: OTPRequest, db: Session = Depends(get_db_connection)):
    try:
        return auth_controller.request_otp(db, otp_data)
    except HTTPException as e:
        return e

@router.post("/auth/reset_password", response_model=AuthResponse)
async def reset_user_password(reset_data: ResetPasswordRequest, db: Session = Depends(get_db_connection)):
    try:
        return auth_controller.reset_user_password(db, reset_data)
    except HTTPException as e:
        return e