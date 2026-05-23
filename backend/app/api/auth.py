from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 

from app.db.postgres import get_db
from app.schemas import user as user_schemas
from app.crud import user as user_crud

# Create the router instance
router = APIRouter()

@router.post(
    "/register",
    response_model=user_schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user: user_schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user.
    Validates that the email and username are not already taken.
    """

    # 1. Check if the email is already registered
    db_user_email = await user_crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already in use."
        )
    
    # 2. Check if the username is already taken
    db_user_username = await user_crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    # 3. Create the user and return the safe response
    # fastapi automatically filters the output through UserResponse
    # ensuring the hashed password is stripped out.
    new_user = await user_crud.create_user(db=db, user=user)
    return new_user