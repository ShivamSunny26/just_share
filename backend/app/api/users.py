from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.postgres import get_db
from app.crud import user as user_crud
from app.schemas import user as user_schemas
from app.api.deps import get_current_user_id

router = APIRouter()

@router.get("/search", response_model=List[user_schemas.UserSearchResponse])
async def search_for_users(
    q: str = Query(..., min_length=1, description="search by username or name"),
    db: AsyncSession = Depends(get_db),
    get_current_user_id: UUID = Depends(get_current_user_id)
):
    users = await user_crud.search_users(
        db=db,
        current_user_id=get_current_user_id,
        search_query=q,
        limit=20
    )

    return users


