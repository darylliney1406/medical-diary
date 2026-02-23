import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate, UserOut, PasswordResetTokenResponse
from ..services.auth import create_user, create_password_reset_token, hash_password
from .deps import get_admin_user

router = APIRouter()


@router.get("", response_model=list[UserOut])
async def list_users(
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    body: UserCreate,
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    return await create_user(session, email=body.email, password=body.password, name=body.name, role=body.role)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.name is not None:
        user.name = body.name
    if body.role is not None:
        user.role = body.role
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await session.commit()


@router.post("/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await session.commit()


@router.post("/{user_id}/request-password-reset", response_model=PasswordResetTokenResponse)
async def request_password_reset(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_password_reset_token(user.id)
    return PasswordResetTokenResponse(reset_token=token)
