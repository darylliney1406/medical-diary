from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from ..models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.user


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    role: UserRole | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime


class UserInToken(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    mfa_enabled: bool


class PasswordResetTokenResponse(BaseModel):
    reset_token: str
    message: str = "Send this token to the user to reset their password."
