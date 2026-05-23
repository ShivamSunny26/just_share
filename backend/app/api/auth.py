from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.db.postgres import get_db
from app.schemas import user as user_schemas
from app.crud import user as user_crud
from app.core.security import verify_password
from app.core.jwt import SECRET_KEY, ALGORITHM, create_access_token, create_refresh_token

# Create the router instance
router = APIRouter()

# @router.post(
#     "/register",
#     response_model=user_schemas.UserResponse,
#     status_code=status.HTTP_201_CREATED
# )
# async def register_user(
#     user: user_schemas.UserCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Registers a new user.
#     Validates that the email and username are not already taken.
#     """

#     # 1. Check if the email is already registered
#     db_user_email = await user_crud.get_user_by_email(db, email=user.email)
#     if db_user_email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email address is already in use."
#         )
    
#     # 2. Check if the username is already taken
#     db_user_username = await user_crud.get_user_by_username(db, username=user.username)
#     if db_user_username:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username is already taken"
#         )
    
#     # 3. Create the user and return the safe response
#     # fastapi automatically filters the output through UserResponse
#     # ensuring the hashed password is stripped out.
#     new_user = await user_crud.create_user(db=db, user=user)
#     return new_user


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
    # 1. Hit the database exactly once
    existing_user = await user_crud.check_existing_user(
        db,
        username=user.username,
        email=user.email
    )

    # 2. Check which field triggered the conflict in Python memory
    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detial="Email already registered"
            )
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detial= "Username already taken"
            )
        
    # If no conflicts, create the user
    new_user = await user_crud.create_user(db=db, user=user)
    return new_user

@router.post("/login", response_model=user_schemas.Token)
async def login_user(
    credentials: user_schemas.UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user, sets a 7-days Refresh Token in an HTTP-only cookie
    and returns a 30-minute Access Token in the JSON body.
    """
    db_user = await user_crud.get_user_by_identifier(
        db,
        identifier=credentials.username_or_email)

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token_payload = {
        "sub": str(db_user.id),
        "email": db_user.email
        }
    
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)

    # 2. Attach the refresh token to the outgoing response as a cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly = True,
        secure = False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )

    # 3. Return ONLY the access token in the JSON body
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
@router.get("/me")
async def get_current_user_profile(token: str = Depends(oauth2_scheme)):
    """A protected route that requires a valid JWT Access Token."""
    try:
        # Decode the token using your secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        
        if user_id is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return {"message": "Success! You accessed a protected route.", "user_id": user_id}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(response: Response):
    """
    Logs out the user by instructing the browser to destroy the 
    HTTP-only refresh token cookie
    """

    # Instruct the browser to delete the cookie by settings it to expir immediately
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/"
    )

    return {
        "message": "Successfully logged out."
    }


@router.post("/refresh",  response_model=user_schemas.Token)
async def refresh_access_token(
    refresh_token: str | None = Cookie(default=None)
):
    """
    Reads the HTTP-only refresh token from the cookie, validates it,
    and returns a fresh 30-minute access token.
    """

    # 1. Ensure the cookie actually exists
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # 2. Decode the token using our secret key
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id=payload.get("sub")
        token_type= payload.get("type")

        # 3. Security Check: Ensure it's not an access token trying to masquerade
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # 4. Mint a brand new 30-minute access token
        new_access_token = create_access_token(data={"sub": user_id})

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please Log in again"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature"
        )
