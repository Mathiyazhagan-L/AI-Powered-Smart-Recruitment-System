from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from .schemas import OtpSendRequest, OtpVerifyRequest
from .service import AuthService
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService(get_settings())


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    return authorization.split(" ", 1)[1].strip()


@router.post("/otp/send")
def send_otp(payload: OtpSendRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    """Generate an OTP for email or phone login."""
    return service.send_otp(payload.method, payload.target)


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifyRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    """Verify OTP, create the user if needed, and return an access token."""
    return service.verify_otp(payload.method, payload.target, payload.code, payload.role)


@router.get("/otp/last")
def get_last_otp(service: AuthService = Depends(get_auth_service)) -> dict:
    """Development helper used by the current HTML design to auto-fill mock OTP."""
    return service.last_otp()


@router.get("/me")
def me(token: str = Depends(bearer_token), service: AuthService = Depends(get_auth_service)) -> dict:
    """Return the logged-in user from a JWT access token."""
    return service.get_current_user(token)


@router.get("/google/login")
def google_login(role: str = Query(default="candidate", pattern="^(candidate|recruiter|admin)$")) -> RedirectResponse:
    """Placeholder Google login route until real OAuth credentials are configured."""
    return RedirectResponse(url=f"/?google_oauth=not_configured&role={role}", status_code=302)
