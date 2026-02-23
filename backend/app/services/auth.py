import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User, UserRole
from ..config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_mfa_token(user_id: uuid.UUID) -> str:
    """Short-lived token issued when MFA is required but not yet validated."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {"sub": str(user_id), "exp": expire, "type": "mfa_pending"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": str(user_id), "exp": expire, "type": "password_reset"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    name: str,
    role: UserRole = UserRole.user,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        name=name,
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
