from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from uuid import UUID
from sqlalchemy.orm import selectinload

from app.models.friend import Friendship, FriendshipStatus


async def send_friend_request(db: AsyncSession, requester_id: UUID, addressee_id: UUID):
    """Scenario 1: User A sends User B a request."""
    stmt = select(Friendship).where(
        or_(
            and_(Friendship.requester_id == requester_id, Friendship.addressee_id == addressee_id),
            and_(Friendship.requester_id == addressee_id, Friendship.addressee_id == requester_id)
        )
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        return existing
    
    new_request = Friendship(
        requester_id=requester_id, 
        addressee_id=addressee_id,
        status = FriendshipStatus.PENDING
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return new_request


async def accept_friend_request(db: AsyncSession, requester_id: UUID, addressee_id: UUID):
    """Scenario 2 : User B accepts User A's request."""
    stmt = select(Friendship).where(
        and_(
            Friendship.requester_id == requester_id, 
            Friendship.addressee_id == addressee_id,
            Friendship.status == FriendshipStatus.PENDING
        )
    )

    result = await db.execute(stmt)
    db_rel = result.scalar_one_or_none()

    if db_rel:
        db_rel.status = FriendshipStatus.ACCEPTED
        await db.commit()
        await db.refresh(db_rel)
    return db_rel

async def reject_friend_request(db: AsyncSession, requester_id: UUID, addressee_id: UUID):
    """Scenario 3: User B rejects User A's request (deletes the row)."""
    stmt = delete(Friendship).where(
        and_(
            Friendship.requester_id == requester_id, 
            Friendship.addressee_id == addressee_id,
            Friendship.status == FriendshipStatus.PENDING
        )
    )
    await db.execute(stmt)
    await db.commit()
    return True

async def block_user(db: AsyncSession, blocker_id: UUID, blocked_id: UUID):
    """Scenario 4: User A blocks User B (deletes any existing relationship and creates a new one with status 'blocked')."""
    # First, delete any existing relationship
    stmt = delete(Friendship).where(
        or_(
            and_(Friendship.requester_id == blocker_id, Friendship.addressee_id == blocked_id),
            and_(Friendship.requester_id == blocked_id, Friendship.addressee_id == blocker_id)
        )
    )
    await db.execute(stmt)

    # Then, create a new relationship with status 'blocked'
    block_rel = Friendship(
        requester_id=blocker_id,
        addressee_id=blocked_id,
        status=FriendshipStatus.BLOCKED
    )
    db.add(block_rel)
    await db.commit()
    await db.refresh(block_rel)
    return block_rel

# async def get_friends_list(db: AsyncSession, user_id: UUID):
#     """Scenario 5: Get all friends for User A"""
#     stmt = select(Friendship).where(
#         and_(
#             or_(
#                 Friendship.requester_id == user_id,
#                 Friendship.addressee_id == user_id
#             ),
#             Friendship.status == FriendshipStatus.ACCEPTED
#         )
#     )
#     result = await db.execute(stmt)
#     return result.scalars().all()

async def check_if_blocked(db: AsyncSession, searcher_id: UUID, target_id: UUID) -> bool:
    """
    Scenario 6: Returns True if the tatget_id blocked the search_id.
    """
    stmt = select(Friendship).where(
        and_(
            Friendship.requester_id == target_id,
            Friendship.addressee_id== searcher_id,
            Friendship.status == FriendshipStatus.BLOCKED
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None

async def get_friends_list(db: AsyncSession, user_id: UUID):
    stmt = (
        select(Friendship)
        .options(
            selectinload(Friendship.requester),
            selectinload(Friendship.addressee)
        )
        .where(
            and_(
                or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_blocked_list(db: AsyncSession, user_id: UUID):

    stmt = select(Friendship).where(
        and_(
            Friendship.requester_id == user_id,
            Friendship.status == FriendshipStatus.BLOCKED
        )
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()