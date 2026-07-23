from __future__ import annotations

import secrets
import time

from fastapi import HTTPException, status

from .repository import AuthRepository
from .security import JwtService
from ..config import Settings


class AuthService:
    """Handles OTP login, local user creation, and token issuing."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo = AuthRepository(settings.local_db_path)
        self.jwt = JwtService(settings.jwt_secret, settings.jwt_expiry_minutes)

    def send_otp(self, method: str, target: str) -> dict:
        normalized_target = self._normalize_target(method, target)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = int(time.time()) + self.settings.otp_expiry_minutes * 60
        self.repo.save_otp(method, normalized_target, code, expires_at)

        return {
            "message": "OTP generated successfully.",
            "method": method,
            "target": normalized_target,
            "expires_in_seconds": self.settings.otp_expiry_minutes * 60,
        }

    def verify_otp(self, method: str, target: str, code: str, role: str) -> dict:
        normalized_target = self._normalize_target(method, target)
        otp = self.repo.get_latest_otp(method, normalized_target)
        if not otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found. Please request a new OTP.")
        if otp["consumed"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP already used. Please request a new OTP.")
        if int(otp["expires_at"]) < int(time.time()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Please request a new OTP.")
        if otp["code"] != code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code.")

        self.repo.consume_otp(otp["id"])
        user = self.repo.get_or_create_user(method, normalized_target, role)
        token = self.jwt.create_access_token(user["id"], user["role"])
        return {"access_token": token, "token_type": "bearer", "user": self.public_user(user)}

    def get_current_user(self, token: str) -> dict:
        payload = self.jwt.verify_token(token)
        user = self.repo.get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
        return self.public_user(user)

    def last_otp(self) -> dict:
        otp = self.repo.get_latest_otp()
        if not otp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No OTP has been generated yet.")
        return {"code": otp["code"], "method": otp["method"], "target": otp["target"], "expires_at": otp["expires_at"]}

    def public_user(self, user: dict) -> dict:
        return {
            "id": user["id"],
            "role": user["role"],
            "email": user.get("email"),
            "phone": user.get("phone"),
            "full_name": user.get("full_name"),
            "profile_completed": bool(user.get("profile_completed")),
        }

    def _normalize_target(self, method: str, target: str) -> str:
        target = target.strip()
        if method == "email":
            return target.lower()
        return target.replace(" ", "")
