from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, status


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


class JwtService:
    """Minimal HS256 JWT service using only Python standard library."""

    def __init__(self, secret: str, expiry_minutes: int) -> None:
        self.secret = secret.encode("utf-8")
        self.expiry_minutes = expiry_minutes

    def create_access_token(self, subject: str, role: str) -> str:
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": subject, "role": role, "iat": now, "exp": now + self.expiry_minutes * 60}
        signing_input = ".".join(
            [
                _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
                _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
            ]
        )
        signature = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{_b64encode(signature)}"

    def verify_token(self, token: str) -> dict[str, Any]:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            signing_input = f"{header_b64}.{payload_b64}"
            expected = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
            received = _b64decode(signature_b64)
            if not hmac.compare_digest(expected, received):
                raise ValueError("Invalid token signature.")
            payload = json.loads(_b64decode(payload_b64))
            if int(payload.get("exp", 0)) < int(time.time()):
                raise ValueError("Token expired.")
            return payload
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc
