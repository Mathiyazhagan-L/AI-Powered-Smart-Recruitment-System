from pydantic import BaseModel, Field


class OtpSendRequest(BaseModel):
    method: str = Field(pattern="^(email|phone)$")
    target: str = Field(min_length=3, max_length=120)


class OtpVerifyRequest(OtpSendRequest):
    code: str = Field(min_length=6, max_length=6)
    role: str = Field(pattern="^(candidate|recruiter|admin)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    role: str
    email: str | None = None
    phone: str | None = None
    full_name: str | None = None
    profile_completed: bool = False
