from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

async def get_user_by_email(db: AsyncSession, email: str):
    """Fetches a user from Postgres by their email address"""
    # Build the async SQL query
    stmt = select(User).where(User.email == email)
    # Execute the query and fetch the first result or None
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str):
    """Fettches a user from Postgres by their username"""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() 

async def create_user(db: AsyncSession, user: UserCreate):
    """Hashes the password and inserts a new user into the Postgres database"""
    # 1. Hash the plain-text password from the pydantic schemas
    hashed_pwd = hash_password(user.password)

    # 2. Create the SQLAlchemy model instance
    db_user = User(
        username = user.username,
        email= user.email,
        hashed_password=hashed_pwd
    )

    # 3. Add to the session and commit the transaction asynchronously
    db.add(db_user)
    await db.commit()

    return db_user
