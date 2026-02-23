import uuid
from datetime import timedelta, timezone, datetime
from fastapi import APIRouter, HTTPException, Response, Cookie, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    LoginRequest, MFAValidateRequest, MFAConfirmRequest, MFADisableRequest,
    PasswordResetRequest, TokenResponse, MFARequiredResponse, MFASetupResponse,
)
from ..schemas.user import UserOut
from ..services.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    create_mfa_token, create_password_reset_token, decode_token,
    get_user_by_id, hash_password, verify_password,
)
from ..config import get_settings
from .deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.mfa_enabled:
        mfa_token = create_mfa_token(user.id)
        return MFARequiredResponse(mfa_required=True, mfa_token=mfa_token)

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.post("/mfa/validate")
async def validate_mfa(
    body: MFAValidateRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(body.mfa_token)
        if payload.get("type") != "mfa_pending":
            raise JWTError()
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token")

    user = await get_user_by_id(session, user_id)
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer", "user": UserOut.model_validate(user)}


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise JWTError()
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(user)
    new_refresh = create_refresh_token(user.id)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")


@router.post("/mfa/setup")
async def mfa_setup(user: User = Depends(get_current_user)) -> MFASetupResponse:
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(name=user.email, issuer_name="MediDiary")
    return MFASetupResponse(qr_uri=qr_uri, secret=secret)


@router.post("/mfa/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_confirm(
    body: MFAConfirmRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    # The secret was returned by /mfa/setup — frontend must pass the code
    # We need the secret temporarily stored; here we accept a secret in body or use pending one.
    # For simplicity: client calls /mfa/setup, stores the secret, then calls /mfa/confirm
    # with the TOTP code. We re-verify with a one-time setup token approach.
    # Simpler: let's accept secret + code in confirm body.
    raise HTTPException(status_code=501, detail="Use /mfa/confirm-with-secret endpoint")


@router.post("/mfa/confirm-with-secret", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_confirm_with_secret(
    body: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    secret = body.get("secret")
    code = body.get("code")
    if not secret or not code:
        raise HTTPException(status_code=400, detail="secret and code required")

    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    user.mfa_secret = secret
    user.mfa_enabled = True
    await session.commit()


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_disable(
    body: MFADisableRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    user.mfa_enabled = False
    user.mfa_secret = None
    await session.commit()


@router.post("/password-reset/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset(
    token: str,
    body: PasswordResetRequest,
    session: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            raise JWTError()
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.hashed_password = hash_password(body.new_password)
    await session.commit()
