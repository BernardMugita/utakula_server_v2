import base64
import json
from fastapi import HTTPException, status
import jwt
import os
import firebase_admin
from firebase_admin import credentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HelperUtils:
    def __init__(self) -> None:
        self.secret_key = os.getenv("ACCESS_SECRET")
        self.algorithm = "HS256"

    def validate_JWT(self, token: str):
        """_summary_

        Args:
            token (str): _description_

        Raises:
            HTTPException: _description_
            HTTPException: _description_

        Returns:
            _type_: _description_
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload  
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
    def initialize_firebase(self):
        """
        Initialize Firebase Admin SDK
        """
        logger.info("Initializing Firebase Admin SDK")
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("/home/jeromemugita/Documents/Code/utakula_server/firebaseCreds.json")
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.info("Firebase Admin SDK already initialized")
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {str(e)}")
            
            
    def decode_google_jwt(token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            return {
                "status": "error",
                "message": "Invalid token",
            }

        base64_url = parts[1]

        # Replace URL-safe characters (same as JS)
        base64_str = base64_url.replace("-", "+").replace("_", "/")

        # Add padding
        padding = 4 - len(base64_str) % 4
        if padding != 4:
            base64_str += "=" * padding

        try:
            # Decode base64
            decoded_bytes = base64.b64decode(base64_str)

            # Parse JSON
            payload = json.loads(decoded_bytes.decode('utf-8'))

            issuers = ['accounts.google.com', 'https://accounts.google.com']
            if payload['iss'] not in issuers:
                return {
                    "status": "error",
                    "message": "Invalid issuer",
                }

            return {
                'status': 'success',
                'data': payload,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }
            