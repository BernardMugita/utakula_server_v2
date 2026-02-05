import base64
import json
from fastapi import HTTPException, status
import jwt
import os
import firebase_admin
from firebase_admin import credentials
import logging
import requests
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HelperUtils:
    def __init__(self) -> None:
        self.secret_key = os.getenv("ACCESS_SECRET")
        self.algorithm = "HS256"
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")  # Add this to your .env

    def validate_JWT(self, token: str):
        """Validate JWT token issued by your application."""
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
        """Initialize Firebase Admin SDK."""
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
            
    @staticmethod
    def decode_google_jwt(token: str) -> Dict:
        """
        Decode and validate Google ID token.
        
        This method:
        1. Decodes the JWT without verification (to extract claims)
        2. Validates the issuer
        3. Optionally validates with Google's tokeninfo endpoint
        
        For production, you should use google-auth library for proper validation.
        """
        logger.info("Decoding Google JWT token")
        
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                logger.error("Invalid token format: does not have 3 parts")
                return {
                    "status": "error",
                    "message": "Invalid token format",
                }

            # Decode the payload (middle part)
            base64_url = parts[1]

            # Replace URL-safe characters
            base64_str = base64_url.replace("-", "+").replace("_", "/")

            # Add padding
            padding = 4 - len(base64_str) % 4
            if padding != 4:
                base64_str += "=" * padding

            # Decode base64
            decoded_bytes = base64.b64decode(base64_str)

            # Parse JSON
            payload = json.loads(decoded_bytes.decode('utf-8'))
            
            logger.info(f"Token decoded for email: {payload.get('email')}")

            # Validate issuer
            valid_issuers = ['accounts.google.com', 'https://accounts.google.com']
            if payload.get('iss') not in valid_issuers:
                logger.error(f"Invalid issuer: {payload.get('iss')}")
                return {
                    "status": "error",
                    "message": "Invalid token issuer",
                }

            # Optional: Verify token with Google (recommended for production)
            # Uncomment if you want additional verification
            # verification_result = HelperUtils._verify_token_with_google(token)
            # if not verification_result:
            #     return {
            #         "status": "error",
            #         "message": "Token verification with Google failed",
            #     }

            logger.info("Token validation successful")
            return {
                'status': 'success',
                'data': payload,
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to parse token: {str(e)}",
            }
        except base64.binascii.Error as e:
            logger.error(f"Base64 decode error: {str(e)}")
            return {
                "status": "error",
                "message": f"Invalid token encoding: {str(e)}",
            }
        except Exception as e:
            logger.exception("Unexpected error decoding token")
            return {
                "status": "error",
                "message": f"Error decoding token: {str(e)}",
            }
    
    @staticmethod
    def _verify_token_with_google(token: str) -> bool:
        """
        Verify token with Google's tokeninfo endpoint.
        
        This provides additional security by validating the token with Google's servers.
        Recommended for production use.
        """
        try:
            response = requests.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={token}',
                timeout=5
            )
            
            if response.status_code == 200:
                token_info = response.json()
                logger.info(f"Google token verification successful for: {token_info.get('email')}")
                return True
            else:
                logger.error(f"Google token verification failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Network error during token verification: {str(e)}")
            return False
        except Exception as e:
            logger.exception("Unexpected error during token verification")
            return False