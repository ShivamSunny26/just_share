from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.postgres import get_db
from app.crud import friend as rel_crud
from app.crud import user as user_crud
from app.schemas import friend as rel_schemas
from app.models.friend import FriendshipStatus
from app.api.deps import get_current_user_id

router = APIRouter()


@router.post("/request/{target_username}", response_model=rel_schemas.FriendshipResponse)
async def send_request(
    target_username: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 1: Send a friend request"""
    target_user = await user_crud.get_user_by_identifier(db, identifier=target_username)
    if not target_user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    target_id = target_user.id
    
    if current_user_id == target_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="Cannot send request to yourself"
        )
    
    is_blocked = await rel_crud.check_if_blocked(db, searcher_id = current_user_id, target_id=target_id)
    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot send request to this user"
        )
    
    rel = await rel_crud.send_friend_request(db, current_user_id, target_id)
    if rel.status != FriendshipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Relationship already exists: {rel.status}"
        )
    return rel

@router.post("/accept/{requester_username}", response_model=rel_schemas.FriendshipResponse)
async def accept_request(
    requester_username: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 2: Accept a friend request"""
    requester = await user_crud.get_user_by_identifier(db, identifier=requester_username)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    rel = await rel_crud.accept_friend_request(db, requester.id, addressee_id=current_user_id)
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending request not found."
        )
    return rel

@router.post("/reject/{requester_username}", status_code=status.HTTP_204_NO_CONTENT)
async def reject_request(
    requester_username: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 3: Reject a friend request"""
    requester = await user_crud.get_user_by_identifier(db, identifier=requester_username)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await rel_crud.reject_friend_request(db, requester.id, addressee_id=current_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending requeste not found"
        )
    return None

@router.post("/block/{target_username}", response_model=rel_schemas.FriendshipResponse)
async def block_user(
    target_username: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 4: Block a user"""
    target_user = await user_crud.get_user_by_identifier(db, identifier=target_username)
    if  not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    target_id = target_user.id
    if current_user_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )
    
    rel = await rel_crud.block_user(db, blocker_id=current_user_id, blocked_id=target_id)
    return rel

@router.get("/friends", response_model=List[rel_schemas.FriendshipResponse])
async def get_friends(
        db: AsyncSession = Depends(get_db),
        current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 5: Get Friend List"""
    friends = await rel_crud.get_friends_list(db, current_user_id)
    return friends

@router.get("/blocked", response_model = List[rel_schemas.FriendshipResponse])
async def get_blocked(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Scenario 6: Get Blocked User List."""
    blocked = await rel_crud.get_blocked_list(db, current_user_id)
    return blocked