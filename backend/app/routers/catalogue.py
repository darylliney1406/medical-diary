import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.entries import FoodCatalogueItem, CatalogueCategory
from ..schemas.entries import FoodCatalogueItemCreate, FoodCatalogueItemUpdate, FoodCatalogueItemOut
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[FoodCatalogueItemOut])
async def list_catalogue(
    search: str | None = Query(default=None),
    category: CatalogueCategory | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(FoodCatalogueItem).where(FoodCatalogueItem.user_id == user.id)
    if search:
        q = q.where(FoodCatalogueItem.name.ilike(f"%{search}%"))
    if category:
        q = q.where(FoodCatalogueItem.category == category)
    result = await session.execute(q.order_by(FoodCatalogueItem.name))
    return result.scalars().all()


@router.post("", response_model=FoodCatalogueItemOut, status_code=status.HTTP_201_CREATED)
async def create_catalogue_item(
    body: FoodCatalogueItemCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = FoodCatalogueItem(user_id=user.id, **body.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.patch("/{item_id}", response_model=FoodCatalogueItemOut)
async def update_catalogue_item(
    item_id: uuid.UUID,
    body: FoodCatalogueItemUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await session.get(FoodCatalogueItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalogue_item(
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await session.get(FoodCatalogueItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    await session.delete(item)
    await session.commit()
