from fastapi import APIRouter, Depends
from schemas.support_schema import SupportRequest, SupportResponse
from controllers.support_controller import SupportController

router = APIRouter(
    prefix="/support",
    tags=["Support"]
)

support_controller = SupportController()

@router.post("/submit", response_model=SupportResponse)
async def submit_support_request(request: SupportRequest):
    """
    Submit a help & support request.
    This will send an email to the support team and an acknowledgment to the user.
    """
    return support_controller.submit_request(request)
