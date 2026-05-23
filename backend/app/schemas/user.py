from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr

# 1. Base Model (shared properties)
# By putting common fields here, we avoid repeating them in the create and Response models
class UserBase(BaseModel):
    username: str
    email: EmailStr

# 2. Registration Payload (Incoming Data)
# Inherits username and email, and strictly requires a plain-text password.
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# 3. Login Payload (Incoming Data)
# Used specifically for the /login endpoint
class UserLogin(BaseModel):
    username_or_email: str
    password: str

# 4. Safe Response Output (Outgoing Data)
# This is what gets sent back to the React Frontend, Notice that 'Password' is completely absent.
class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime 

    # crucial for SQLALchemy compatibility
    # This tells Pydantic to read the data directly from the SQLAlchemy User Model objects.
    model_config = ConfigDict(from_attributes=True)

# 5. JWT Authentication Payload (Outgping Data)
# Standard OAuth2 format for returning secure access tokens
class Token(BaseModel):
    access_token: str
    token_type: str
    