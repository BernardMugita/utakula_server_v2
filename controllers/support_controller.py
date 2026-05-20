from fastapi import HTTPException, status
from schemas.support_schema import SupportRequest, SupportResponse
from services.support_service import SupportService
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class SupportController:
    def __init__(self):
        self.support_service = SupportService()

    def submit_request(self, request: SupportRequest) -> SupportResponse:
        """Handle support request submission"""
        result = self.support_service.process_support_request(request)
        
        try:
        
            if result["status"] == "success":
                return SupportResponse(
                    status="success",
                    message=result["message"]
                )
            else:
                logger.error(f"Support request failed: {result['message']}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"]
                )
        except Exception as e:
          return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=SupportResponse(
                    status="error",
                    message="An error occurred while processing the support request.",
                ).dict()
            )
