from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session
from connect import SessionLocal

from controllers.membership_controller import MembershipController
from schemas.membership_schema import (
    MembershipCreate, MembershipUpdate, MembershipGet, MembershipDelete,
    CreateMembershipResponse, RetrieveMembershipResponse, UpdateMembershipResponse, DeleteMembershipResponse
)

router = APIRouter()
membership_controller = MembershipController()

def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/memberships/create", response_model=CreateMembershipResponse)
async def create_membership(
    membership_data: MembershipCreate,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Create a new membership tier (Admin only)"""
    return membership_controller.create_membership(membership_data, db, authorization)

@router.post("/memberships/get_all", response_model=RetrieveMembershipResponse)
async def get_all_memberships(
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get all active membership tiers"""
    return membership_controller.get_all_memberships(db, authorization)

@router.post("/memberships/get_by_id", response_model=RetrieveMembershipResponse)
async def get_membership(
    membership_data: MembershipGet = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Get specific membership by ID"""
    return membership_controller.get_membership_by_id(membership_data, db, authorization)

@router.post("/memberships/update", response_model=UpdateMembershipResponse)
async def update_membership(
    membership_data: MembershipUpdate,
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Update membership details (Admin only)"""
    return membership_controller.update_membership(membership_data, db, authorization)

@router.post("/memberships/delete", response_model=DeleteMembershipResponse)
async def delete_membership(
    membership_data: MembershipDelete = Body(...),
    db: Session = Depends(get_db_connection),
    authorization: str = Header(...)
):
    """Deactivate membership (Admin only)"""
    return membership_controller.delete_membership(membership_data, db, authorization)