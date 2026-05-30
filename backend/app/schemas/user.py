from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional

# 1. Base Model (shared properties)
# By putting common fields here, we avoid repeating them in the create and Response models
class UserBase(BaseModel):
    username: str
    name: Optional[str] = None
    email: EmailStr
    public_key: Optional[str] = None

    @field_validator("username", "email", "name", mode="before")
    @classmethod
    def to_lowercase(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

# 2. Registration Payload (Incoming Data)
class UserCreate(UserBase):
    password: str = Field(min_length=8)
    

# 3. Login Payload (Incoming Data)
# Used specifically for the /login endpoint
class UserLogin(BaseModel):
    username_or_email: str
    password: str

    @field_validator("username_or_email", mode="before")
    @classmethod
    def login_to_lowercase(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

# 4. Safe Response Output (Outgoing Data)
# This is what gets sent back to the React Frontend, Notice that 'Password' is completely absent.
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime 

    model_config = ConfigDict(from_attributes=True)

# 5. JWT Authentication Payload (Outgping Data)
# Standard OAuth2 format for returning secure access tokens
class Token(BaseModel):
    access_token: str
    token_type: str
    

# 6. Safe search output
class UserSearchResponse(UserBase):
    id: UUID
    friendship_status: str = "none"
    model_config = ConfigDict(from_attributes=True)

class PublicKeyUpdate(BaseModel):
    public_key: str

class PublicKeyResponse(BaseModel):
    username: str
    public_key: str