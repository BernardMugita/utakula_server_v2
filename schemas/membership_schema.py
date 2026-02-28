import uuid
from typing import Optional, Dict, Union, List
from datetime import datetime
from pydantic import BaseModel
from utils.enums import MembershipType, BillingCycle

class MembershipCreate(BaseModel):
    membership_type: MembershipType
    membership_name: str
    membership_description: Optional[str] = None
    membership_price: float
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    features: Optional[Dict] = {}
    is_active: bool = True

class MembershipUpdate(BaseModel):
    membership_id: uuid.UUID
    membership_name: Optional[str] = None
    membership_description: Optional[str] = None
    membership_price: Optional[float] = None
    billing_cycle: Optional[BillingCycle] = None
    features: Optional[Dict] = None
    is_active: Optional[bool] = None

class MembershipRead(BaseModel):
    membership_id: uuid.UUID
    membership_type: MembershipType
    membership_name: str
    membership_description: Optional[str] = None
    membership_price: float
    billing_cycle: BillingCycle
    features: Optional[Dict] = {}
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MembershipGet(BaseModel):
    membership_id: uuid.UUID

class MembershipDelete(BaseModel):
    membership_id: uuid.UUID

class CreateMembershipResponse(BaseModel):
    status: str
    message: str
    payload: Union[MembershipRead, str]

class RetrieveMembershipResponse(BaseModel):
    status: str
    message: str
    payload: Union[MembershipRead, List[MembershipRead], str]

class UpdateMembershipResponse(BaseModel):
    status: str
    message: str
    payload: Union[MembershipRead, str]

class DeleteMembershipResponse(BaseModel):
    status: str
    payload: str