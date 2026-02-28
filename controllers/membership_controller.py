from fastapi import HTTPException, status, Header, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.membership_model import MembershipModel
from schemas.membership_schema import (
    MembershipCreate, MembershipRead, MembershipUpdate, MembershipGet, MembershipDelete,
    CreateMembershipResponse, RetrieveMembershipResponse, UpdateMembershipResponse, DeleteMembershipResponse
)
from utils.helper_utils import HelperUtils

utils = HelperUtils()

class MembershipController:
    def __init__(self) -> None:
        pass
    
    def create_membership(self, membership: MembershipCreate, db: Session, authorization: str = Header(...)):
        """Create a new membership tier (Admin only)"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            if payload['role'] != "admin":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=CreateMembershipResponse(
                        status="error",
                        message="Unauthorized",
                        payload="You are not authorized to access this route"
                    ).dict()
                )
            
            # Check if membership type already exists
            existing_membership = db.query(MembershipModel).filter(
                MembershipModel.membership_type == membership.membership_type
            ).first()
            
            if existing_membership:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=CreateMembershipResponse(
                        status="error",
                        message="Failed to create membership",
                        payload=f"Membership type '{membership.membership_type.value}' already exists"
                    ).dict()
                )
            
            new_membership = MembershipModel(
                membership_type=membership.membership_type,
                membership_name=membership.membership_name,
                membership_description=membership.membership_description,
                membership_price=membership.membership_price,
                billing_cycle=membership.billing_cycle,
                features=membership.features,
                is_active=membership.is_active
            )
            
            db.add(new_membership)
            db.commit()
            db.refresh(new_membership)
            
            return CreateMembershipResponse(
                status="success",
                message="Membership tier created successfully",
                payload=MembershipRead.from_orm(new_membership)
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=CreateMembershipResponse(
                    status="error",
                    message="Error creating membership",
                    payload=str(e)
                ).dict()
            )
    
    def get_all_memberships(self, db: Session, authorization: str = Header(...)):
        """Get all membership tiers"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            memberships = db.query(MembershipModel).filter(MembershipModel.is_active == True).all()
            
            membership_list = [MembershipRead.from_orm(m) for m in memberships]
            
            return RetrieveMembershipResponse(
                status="success",
                message="List of all active memberships",
                payload=membership_list
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveMembershipResponse(
                    status="error",
                    message="Error retrieving memberships",
                    payload=str(e)
                ).dict()
            )
    
    def get_membership_by_id(self, membership_data: MembershipGet, db: Session, authorization: str = Header(...)):
        """Get a specific membership by ID"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            utils.validate_JWT(token)
            
            membership = db.query(MembershipModel).filter(
                MembershipModel.id == str(membership_data.membership_id)
            ).first()
            
            if not membership:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=RetrieveMembershipResponse(
                        status="error",
                        message="Membership not found",
                        payload="The requested membership does not exist"
                    ).dict()
                )
            
            return RetrieveMembershipResponse(
                status="success",
                message="Membership details",
                payload=MembershipRead.from_orm(membership)
            )
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=RetrieveMembershipResponse(
                    status="error",
                    message="Error retrieving membership",
                    payload=str(e)
                ).dict()
            )
    
    def update_membership(self, membership_data: MembershipUpdate, db: Session, authorization: str = Header(...)):
        """Update membership details (Admin only)"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            if payload['role'] != "admin":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=UpdateMembershipResponse(
                        status="error",
                        message="Unauthorized",
                        payload="You are not authorized to access this route"
                    ).dict()
                )
            
            membership = db.query(MembershipModel).filter(
                MembershipModel.id == str(membership_data.membership_id)
            ).first()
            
            if not membership:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=UpdateMembershipResponse(
                        status="error",
                        message="Membership not found",
                        payload="The requested membership does not exist"
                    ).dict()
                )
            
            if membership_data.membership_name is not None:
                membership.membership_name = membership_data.membership_name
            if membership_data.membership_description is not None:
                membership.membership_description = membership_data.membership_description
            if membership_data.membership_price is not None:
                membership.membership_price = membership_data.membership_price
            if membership_data.billing_cycle is not None:
                membership.billing_cycle = membership_data.billing_cycle
            if membership_data.features is not None:
                membership.features = membership_data.features
            if membership_data.is_active is not None:
                membership.is_active = membership_data.is_active
            
            db.commit()
            db.refresh(membership)
            
            return UpdateMembershipResponse(
                status="success",
                message="Membership updated successfully",
                payload=MembershipRead.from_orm(membership)
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=UpdateMembershipResponse(
                    status="error",
                    message="Error updating membership",
                    payload=str(e)
                ).dict()
            )
    
    def delete_membership(self, membership_data: MembershipDelete, db: Session, authorization: str = Header(...)):
        """Delete membership (Admin only, soft delete by setting is_active=False)"""
        try:
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header must start with 'Bearer '"
                )
            
            token = authorization[7:]
            payload = utils.validate_JWT(token)
            
            if payload['role'] != "admin":
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=DeleteMembershipResponse(
                        status="error",
                        payload="You are not authorized to access this route"
                    ).dict()
                )
            
            membership = db.query(MembershipModel).filter(
                MembershipModel.id == str(membership_data.membership_id)
            ).first()
            
            if not membership:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=DeleteMembershipResponse(
                        status="error",
                        payload="Membership not found"
                    ).dict()
                )
            
            # Soft delete
            membership.is_active = False
            db.commit()
            
            return DeleteMembershipResponse(
                status="success",
                payload="Membership deactivated successfully"
            )
            
        except Exception as e:
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=DeleteMembershipResponse(
                    status="error",
                    payload=f"Error deleting membership: {str(e)}"
                ).dict()
            )