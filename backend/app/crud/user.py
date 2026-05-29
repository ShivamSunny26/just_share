from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from sqlalchemy import or_, case, desc, and_
from uuid import UUID
from app.models.friend import Friendship, FriendshipStatus


async def get_user_by_identifier(db: AsyncSession, identifier: str):
    """Fetch a user from Postgres by matching Either their email or username"""
    stmt = select(User).where(
        or_(
            User.email == identifier, 
            User.username == identifier,
            User.name == identifier
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def check_existing_user(db: AsyncSession, username: str, email: str):
    """Checks if a user already exists with either the given email or username in a single query"""
    stmt = select(User).where(
        or_(
            User.username == username,
            User.email == email
        )
    )
    result= await db.execute(stmt)
    return result.scalar_one_or_none()

# async def get_user_by_email(db: AsyncSession, email: str):
#     """Fetches a user from Postgres by their email address"""
#     # Build the async SQL query
#     stmt = select(User).where(User.email == email)
#     # Execute the query and fetch the first result or None
#     result = await db.execute(stmt)
#     return result.scalar_one_or_none()

# async def get_user_by_username(db: AsyncSession, username: str):
#     """Fettches a user from Postgres by their username"""
#     stmt = select(User).where(User.username == username)
#     result = await db.execute(stmt)
#     return result.scalar_one_or_none() 

async def create_user(db: AsyncSession, user: UserCreate):
    """Hashes the password and inserts a new user into the Postgres database"""
    # 1. Hash the plain-text password from the pydantic schemas
    hashed_pwd = hash_password(user.password)

    # 2. Create the SQLAlchemy model instance
    db_user = User(
        username = user.username,
        name = user.name,
        email= user.email,
        hashed_password=hashed_pwd
    )

    # 3. Add to the session and commit the transaction asynchronously
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

async def search_users(db: AsyncSession, current_user_id: UUID, search_query: str, limit: int = 15):
    wildcard_query = f"%{search_query}%"
    prefix_query= f"{search_query}%"

    friendship_condition = or_(
        and_(Friendship.requester_id == current_user_id, Friendship.addressee_id == User.id),
        and_(Friendship.requester_id == User.id, Friendship.addressee_id == current_user_id)
    )

    relevance_score = case(
        (User.username.ilike(search_query), 4),
        (User.username.ilike(prefix_query), 3),
        (User.name.ilike(prefix_query), 2),
        else_ = 1
    )

    # Friendship score (Friends jumps to the top of the list)
    friend_score = case(
        (Friendship.status == FriendshipStatus.ACCEPTED, 2),
        (Friendship.status == FriendshipStatus.PENDING, 1),
        else_=0
    )
    
    # Join the USer and Friendship tables
    stmt = (
        select(User, Friendship.status.label("friendship_status"))
        .outerjoin(Friendship, friendship_condition)
        .where(
            and_(
                User.id != current_user_id,
                or_(
                    User.username.ilike(wildcard_query),
                    User.name.ilike(wildcard_query)
                )
            )
        )
        .order_by(
            desc(friend_score),
            desc(relevance_score),
            User.username
        )
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    search_results = []
    for user_obj, status_enum in rows:
        status_str = status_enum.value if status_enum else "none"

        search_results.append({
            "id": user_obj.id,
            "username": user_obj.name,
            "name": user_obj.name,
            "email": user_obj.email, 
            "friendship_status": status_str
        })


    return search_results