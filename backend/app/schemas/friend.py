from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.friend import FriendshipStatus

class FriendshipBase(BaseModel):
    requester_id: UUID
    addressee_id: UUID
    status: FriendshipStatus


class FriendshipResponse(FriendshipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfileMinimal(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None

    class Config: 
        from_attributes = True



