from pydantic import BaseModel, EmailStr
from .user import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MFAValidateRequest(BaseModel):
    mfa_token: str
    code: str


class MFAConfirmRequest(BaseModel):
    code: str


class MFADisableRequest(BaseModel):
    code: str


class PasswordResetRequest(BaseModel):
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut | None = None


class MFARequiredResponse(BaseModel):
    mfa_required: bool = True
    mfa_token: str


class MFASetupResponse(BaseModel):
    qr_uri: str
    secret: str
