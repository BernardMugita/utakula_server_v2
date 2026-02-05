# user_controller.py
from sqlalchemy.orm import Session
from models.user_model import UserModel
from schemas.user_schema import (
    OTPRequest, 
    RegisterResponse, 
    ResetPasswordRequest, 
    UserAuthorize, 
    UserCreate, 
    UserRead, 
    SignedUser, 
    AuthResponse
)
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from services.email_services import EmailService
import jwt
import random
import os
from dotenv import load_dotenv
import logging

from utils.helper_utils import HelperUtils

load_dotenv()

SECRET_KEY = os.getenv("ACCESS_SECRET")
ALGORITHM = "HS256"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

email_service = EmailService()
helpers = HelperUtils()

class AuthController:
    def __init__(self):
        pass

    def hash_password(self, password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def generate_jwt_token(self, user: SignedUser | dict) -> str:
        """Generate a JWT token for the user."""
        # Handle both SignedUser objects and dicts
        if isinstance(user, dict):
            payload = {
                "user_id": user.get("id"),
                "username": user.get("username"),
                "role": user.get("role"),
                "exp": datetime.utcnow() + timedelta(days=4)
            }
        else:
            payload = {
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "exp": datetime.utcnow() + timedelta(days=4)
            }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_user_account(self, user_data: UserCreate, db: Session) -> UserRead:
        """Create a new user account with email/password."""
        try:
            # Check if the user already exists by email or username
            existing_user = db.query(UserModel).filter(
                (UserModel.email == user_data.email) |
                (UserModel.username == user_data.username)
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists."
                )

            # Create a new user and hash the password
            new_user = UserModel(
                username=user_data.username,
                email=user_data.email,
            )
            new_user.set_password(user_data.password)

            # Add to the database and commit
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # send welcome email
            email_service.send_welcome_email(new_user.email, new_user.username)

            # Create a UserRead instance to return
            user_response = UserRead(
                id=new_user.id,
                username=new_user.username,
                role=new_user.role,
                email=new_user.email
            )

            # Return a successful response with the user details and status code 201
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=RegisterResponse(
                    status="success",
                    message="Account created successfully.",
                    payload=str(user_response)
                ).dict()
            )

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AuthResponse(
                    status="error",
                    message="Registration failed",
                    payload=f"{str(e)}"
                ).dict()
            )
            
    def authorize_user_account(self, user_data: UserAuthorize, db: Session) -> JSONResponse:
        """Authorize user with username/password and return JWT token."""
        try:
            # Check if the user exists
            existing_user = db.query(UserModel).filter(
                UserModel.username == user_data.username
            ).first()

            if not existing_user:
                # Return 400 error if user not found
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=AuthResponse(
                        status="error",
                        message="404",
                        payload="User account does not exist."
                    ).dict()
                )
        
            # Verify the password
            if not existing_user.verify_password(user_data.password):
                # Return 401 error if password is incorrect
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=AuthResponse(
                        status="error",
                        message="Failed. Try again!",
                        payload="Incorrect password."
                    ).dict()
                )
            
            # Generate JWT token for the user
            token = self.generate_jwt_token(
                SignedUser(
                    id=str(existing_user.id),
                    username=existing_user.username,
                    role=existing_user.role,
                )
            )
        
            # Return 200 success response with token payload
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=AuthResponse(
                    status="success",
                    message="Authorized",
                    payload=token
                ).dict()
            )
            
        except Exception as e:
            # Return 500 error on any unexpected failure
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AuthResponse(
                    status="error",
                    message="Account authorization failed",
                    payload=f"{str(e)}"
                ).dict()
            )
            
    def google_sign_up(self, data: dict, db: Session) -> JSONResponse:
        """
        Handle Google OAuth sign-up or sign-in.
        
        Args:
            data: Dictionary with 'token' key containing Google ID token
            db: Database session
            
        Returns:
            JSONResponse with status, message, and JWT token payload
        """
        logger.info("===== GOOGLE OAUTH REQUEST RECEIVED =====")
        logger.info(f"Request data keys: {data.keys()}")
        
        try:
            # Step 1: Validate that token exists
            if 'token' not in data:
                logger.error("Missing 'token' in request data")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=AuthResponse(
                        status="error",
                        message="Missing required field: token",
                        payload="No token provided"
                    ).dict()
                )
            
            logger.info(f"Token received, length: {len(data['token'])}")
            
            # Step 2: Decode and validate Google JWT token
            decoded_data = helpers.decode_google_jwt(data['token'])
            logger.info(f"Token decode status: {decoded_data.get('status')}")
            
            if decoded_data.get("status") == "error":
                logger.error(f"Token validation failed: {decoded_data.get('message')}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=AuthResponse(
                        status="error",
                        message=decoded_data.get("message", "Token validation failed"),
                        payload="Invalid Google token"
                    ).dict()
                )
            
            user_data = decoded_data['data']
            logger.info(f"Token validated for user: {user_data.get('email')}")
            
            # Step 3: Validate required fields in decoded token
            required_fields = ["sub", "email", "name"]
            for field in required_fields:
                if field not in user_data:
                    logger.error(f"Missing field in token: {field}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content=AuthResponse(
                            status="error",
                            message=f"Missing required field in token: {field}",
                            payload=f"Token missing {field}"
                        ).dict()
                    )
            
            # Step 4: Check if user exists with this Google ID
            existing_google_user = db.query(UserModel).filter(
                UserModel.google_oauth_id == user_data["sub"]
            ).first()
            
            if existing_google_user:
                logger.info(f"Existing Google user found: {existing_google_user.email}")
                token = self.generate_jwt_token(existing_google_user.to_dict())
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=AuthResponse(
                        status="success",
                        message="Google OAuth login successful",
                        payload=token
                    ).dict()
                )
            
            # Step 5: Check if email already exists (account linking)
            existing_email_user = db.query(UserModel).filter(
                UserModel.email == user_data["email"]
            ).first()
            
            if existing_email_user:
                logger.info(f"Email exists, linking Google account: {existing_email_user.email}")
                
                if existing_email_user.google_oauth_id:
                    # Email already linked to different Google account
                    logger.warning(f"Email already linked to Google account: {user_data['email']}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content=AuthResponse(
                            status="error",
                            message="Email already linked with another Google account",
                            payload="duplicate_google_link"
                        ).dict()
                    )
                else:
                    # Link Google account to existing email user
                    existing_email_user.google_oauth_id = user_data["sub"]
                    
                    if existing_email_user._password_hash:
                        existing_email_user.login_type = "both"
                    else:
                        existing_email_user.login_type = "google_oauth"
                    
                    db.commit()
                    db.refresh(existing_email_user)
                    
                    token = self.generate_jwt_token(existing_email_user.to_dict())
                    
                    logger.info("Google account linked successfully")
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content=AuthResponse(
                            status="success",
                            message="Google account linked successfully",
                            payload=token
                        ).dict()
                    )
            
            # Step 6: Create new user
            logger.info(f"Creating new user via Google OAuth: {user_data['email']}")
            new_user = UserModel(
                email=user_data["email"],
                username=user_data["name"],
                google_oauth_id=user_data["sub"],
                login_type="google_oauth"
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            token = self.generate_jwt_token(new_user.to_dict())
            
            logger.info("New user created successfully via Google OAuth")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=AuthResponse(
                    status="success",
                    message="User registered via Google OAuth successfully",
                    payload=token
                ).dict()
            )
                    
        except Exception as e:
            logger.exception("Exception in google_sign_up")
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AuthResponse(
                    status="error",
                    message="Error with Google OAuth sign-up",
                    payload=str(e)
                ).dict()
            )
        
    def request_otp(self, db: Session, otp_data: OTPRequest) -> JSONResponse:
        """Generate and return a one-time password (OTP) for the user."""
        try: 
            otp = str(random.randint(100000, 999999))
        
            existing_user = db.query(UserModel).filter(UserModel.email == otp_data.email).first()
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            send_email_request = email_service.send_OTP_via_SMTP(otp_data.email, otp)

            if send_email_request.get("status") != "success":
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=AuthResponse(
                        status="error",
                        message="Failed to send OTP email",
                        payload=f"{send_email_request.get('message')}"
                    ).dict()
                )
            
            existing_user._password_hash = otp
            db.commit()
            db.refresh(existing_user)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=AuthResponse(
                    status="success",
                    message="OTP generated successfully",
                    payload=otp
                ).dict()
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AuthResponse(
                    status="error",
                    message="Error generating OTP",
                    payload=str(e)
                ).dict()
            )

    def reset_user_password(self, db: Session, reset_data: ResetPasswordRequest) -> JSONResponse:
        """Reset the user's password."""
        try:
            user = db.query(UserModel).filter(UserModel.email == reset_data.email).first()
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=AuthResponse(
                        status="error",
                        message="User not found",
                        payload="No account associated with this email."
                    ).dict()
                )

            if user._password_hash != reset_data.otp:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=AuthResponse(
                        status="error",
                        message="Invalid OTP",
                        payload="The provided OTP is incorrect."
                    ).dict()
                )
            
            # Hash the new password and update
            hashed_password = self.hash_password(reset_data.new_password)
            user._password_hash = hashed_password
            db.commit()
            db.refresh(user)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=AuthResponse(
                    status="success",
                    message="Password reset successfully",
                    payload="Your password has been updated."
                ).dict()
            )

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AuthResponse(
                    status="error",
                    message="Error resetting password",
                    payload=str(e)
                ).dict()
            )