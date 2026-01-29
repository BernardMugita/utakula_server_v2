# user_controller.py
from sqlalchemy.orm import Session
from models.user_model import UserModel
from schemas.user_schema import OTPRequest, RegisterResponse, ResetPasswordRequest, UserAuthorize, UserCreate, UserRead, SignedUser, AuthResponse
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from services.email_services import EmailService
import jwt
import random
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("ACCESS_SECRET")
ALGORITHM = "HS256"

# Configure the password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

email_service = EmailService()

class AuthController:
    def __init__(self):
        pass

    def hash_password(self, password: str) -> str:
        """Hash a plain password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def generate_jwt_token(self, user: SignedUser) -> str:
        """Generate a JWT token for the user."""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(days=4)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_user_account(self, user_data: UserCreate, db: Session) -> UserRead:
        """_summary_

        Args:
            user_data (UserCreate): _description_
            db (Session): _description_

        Raises:
            HTTPException: _description_

        Returns:
            UserRead: _description_
        """

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
        """_summary_

        Args:
            user_data (UserAuthorize): _description_
            db (Session): _description_

        Returns:
            JSONResponse: _description_
        """
        
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
        """Reset the user's password.

        Args:
            db (Session): Database session.
            email (str): User's email.
            new_password (str): New password to set.

        Returns:
            JSONResponse: Response indicating success or failure.
        """
        
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
