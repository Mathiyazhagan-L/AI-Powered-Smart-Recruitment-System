from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4


class AuthRepository:
    """JSON-file persistence for local auth development."""

    _lock = threading.Lock()

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_store()

    def _init_store(self) -> None:
        with self._lock:
            if not self.db_path.exists() or not self.db_path.read_text(encoding="utf-8", errors="ignore").strip():
                self._write({"users": [], "otp_codes": []})

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"users": [], "otp_codes": []}

    def _write(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save_otp(self, method: str, target: str, code: str, expires_at: int) -> None:
        with self._lock:
            data = self._read()
            data["otp_codes"].append(
                {
                    "id": uuid4().hex,
                    "method": method,
                    "target": target,
                    "code": code,
                    "expires_at": expires_at,
                    "consumed": False,
                    "created_at": len(data["otp_codes"]) + 1,
                }
            )
            self._write(data)

    def get_latest_otp(self, method: str | None = None, target: str | None = None) -> dict[str, Any] | None:
        data = self._read()
        otps = data["otp_codes"]
        if method:
            otps = [otp for otp in otps if otp["method"] == method]
        if target:
            otps = [otp for otp in otps if otp["target"] == target]
        return otps[-1] if otps else None

    def consume_otp(self, otp_id: str) -> None:
        with self._lock:
            data = self._read()
            for otp in data["otp_codes"]:
                if otp["id"] == otp_id:
                    otp["consumed"] = True
                    break
            self._write(data)

    def get_or_create_user(self, method: str, target: str, role: str) -> dict[str, Any]:
        column = "email" if method == "email" else "phone"
        with self._lock:
            data = self._read()
            for user in data["users"]:
                if user.get(column) == target and user.get("role") == role:
                    return user

            user = {
                "id": uuid4().hex,
                "role": role,
                "email": target if method == "email" else None,
                "phone": target if method == "phone" else None,
                "full_name": None,
                "profile_completed": False,
            }
            data["users"].append(user)
            self._write(data)
            return user

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        data = self._read()
        return next((user for user in data["users"] if user["id"] == user_id), None)
