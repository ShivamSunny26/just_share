import jwt
from datetime import datetime, timedelta, timezone
import os



# Load JWT settings from the environment
SECRET_KEY=os.getenv("SECRET_KEY", "fallback_secret_key_for_dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))



# JWT Token Generation

def create_access_token(data: dict) -> str:
    """Creates a securely signed JWT"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict)-> str:
    """Creates a long-lived refresh token (7days)"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)