from services.email_services import EmailService
from schemas.support_schema import SupportRequest
import logging

logger = logging.getLogger(__name__)

class SupportService:
    """Service to handle help and support requests"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.support_email = "support@utakula.co.ke"

    def process_support_request(self, request: SupportRequest) -> dict:
        """
        Process a support request by sending an email to the support team
        and an acknowledgment email to the user.
        """
        try:
            # 1. Send email to support team
            team_res = self.email_service.send_support_email(
                recipient_email=self.support_email,
                user_name=request.name,
                user_email=request.email,
                subject=request.subject,
                message=request.message
            )
            
            if team_res["status"] == "error":
                logger.error(f"Failed to send support email to team: {team_res['message']}")
                # We still try to send acknowledgment to user if team email fails? 
                # Probably better to return error if team doesn't get it.
                return team_res

            # 2. Send acknowledgment to user
            user_res = self.email_service.send_acknowledgment_email(
                recipient_email=request.email,
                user_name=request.name,
                subject=request.subject,
                message=request.message
            )
            
            if user_res["status"] == "error":
                logger.warning(f"Failed to send acknowledgment email to user: {user_res['message']}")
                # We don't necessarily want to fail the whole request if only the acknowledgment fails,
                # but we should let the caller know if needed. 
                # For now, we'll return success if the team got the message.
            
            return {
                "status": "success",
                "message": "Support request submitted successfully."
            }
            
        except Exception as e:
            logger.error(f"Unexpected error processing support request: {str(e)}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
