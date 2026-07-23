from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ==========================
# Send OTP (legacy)
# ==========================

class SendOTPRequest(BaseModel):

    method: str = Field(
        ...,
        description="email or phone"
    )

    target: str

    intent: Optional[str] = Field(None, description="register, reset_password, etc.")


# ==========================
# Verify OTP (legacy)
# ==========================

class VerifyOTPRequest(BaseModel):

    method: str

    target: str

    code: str = Field(
        ...,
        min_length=6,
        max_length=6
    )

    role: str


# ==========================
# Register — Step 1
# ==========================

class RegisterRequest(BaseModel):

    full_name: str = Field(..., min_length=2, max_length=100)

    email: EmailStr

    otp_code: str = Field(..., min_length=6, max_length=6)

    mobile_number: str = Field(..., min_length=10, max_length=15)

    password: str = Field(..., min_length=8, max_length=256)

    confirm_password: str = Field(..., min_length=8, max_length=256)

    role: str = Field(..., description="candidate or company")


# ==========================
# Register — Step 2 (OTP Verify)
# ==========================

class VerifyRegistrationRequest(BaseModel):

    email: EmailStr

    otp_code: str = Field(..., min_length=6, max_length=6)


# ==========================
# Login
# ==========================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str

    remember_me: Optional[bool] = False


# ==========================
# Forgot Password — Request OTP
# ==========================

class ForgotPasswordRequest(BaseModel):

    email: EmailStr


# ==========================
# Reset Password
# ==========================

class ResetPasswordRequest(BaseModel):

    email: EmailStr

    otp_code: str = Field(..., min_length=6, max_length=6)

    new_password: str = Field(..., min_length=8, max_length=256)

    confirm_password: str = Field(..., min_length=8, max_length=256)


# ==========================
# Google Auth
# ==========================

class GoogleVerifyRequest(BaseModel):
    """
    Sent by frontend containing the JWT credential from Google Identity Services.
    """
    credential: str


class GoogleCompleteRequest(BaseModel):
    """
    Sent when a new Google user needs to supply mobile number + role.
    The google_id and email come from the server-side token verification result
    stored temporarily in the response.
    """

    google_id: str

    email: EmailStr

    full_name: str

    mobile_number: str = Field(..., min_length=10, max_length=15)

    role: str = Field(..., description="candidate or company")


# ==========================
# User Response
# ==========================

class UserResponse(BaseModel):

    id: int

    email: Optional[str]

    phone: Optional[str]

    role: str

    full_name: Optional[str]

    email_verified: bool

    phone_verified: bool

    is_active: bool

    is_verified: bool

    auth_provider: Optional[str]

    model_config = {
        "from_attributes": True,
    }


# ==========================
# Token Response
# ==========================

class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserResponse