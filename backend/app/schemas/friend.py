from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.friend import FriendshipStatus

class FriendshipBase(BaseModel):
    requester_id: UUID
    addressee_id: UUID
    status: FriendshipStatus


class FriendUserDetail(BaseModel):
    id: UUID
    username: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FriendshipResponse(FriendshipBase):
    id: UUID
    created_at: datetime
    
    requester: FriendUserDetail | None = None
    addressee: FriendUserDetail | None = None
    model_config = ConfigDict(from_attributes=True)

class UserProfileMinimal(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None

    class Config: 
        from_attributes = True



