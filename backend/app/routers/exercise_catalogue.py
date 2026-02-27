import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.entries import ExerciseCatalogueItem
from ..schemas.entries import ExerciseCatalogueItemCreate, ExerciseCatalogueItemOut
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[ExerciseCatalogueItemOut])
async def list_exercise_catalogue(
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(ExerciseCatalogueItem).where(ExerciseCatalogueItem.user_id == user.id)
    if search:
        q = q.where(ExerciseCatalogueItem.name.ilike(f"%{search}%"))
    result = await session.execute(q.order_by(ExerciseCatalogueItem.name))
    return result.scalars().all()


@router.post("", response_model=ExerciseCatalogueItemOut, status_code=status.HTTP_201_CREATED)
async def create_exercise_catalogue_item(
    body: ExerciseCatalogueItemCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Avoid duplicates (case-insensitive)
    existing = await session.execute(
        select(ExerciseCatalogueItem).where(
            ExerciseCatalogueItem.user_id == user.id,
            ExerciseCatalogueItem.name.ilike(body.name),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Exercise already exists in catalogue")
    item = ExerciseCatalogueItem(user_id=user.id, name=body.name)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise_catalogue_item(
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await session.get(ExerciseCatalogueItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Exercise catalogue item not found")
    await session.delete(item)
    await session.commit()
