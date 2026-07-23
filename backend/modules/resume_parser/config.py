from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_key: str | None = Field(default=None, alias="SUPABASE_KEY")
    supabase_storage_bucket: str = Field(default="resumes", alias="SUPABASE_STORAGE_BUCKET")
    upload_dir: Path = Field(default=Path("uploads"), alias="UPLOAD_DIR")
    local_db_path: Path = Field(default=Path("app_data/aihire_auth.json"), alias="LOCAL_DB_PATH")
    frontend_dir: Path | None = Field(default=Path("C:/Recruitment"), alias="FRONTEND_DIR")
    jwt_secret: str = Field(default="change-this-secret-in-production", alias="JWT_SECRET")
    jwt_expiry_minutes: int = Field(default=24 * 60, alias="JWT_EXPIRY_MINUTES")
    otp_expiry_minutes: int = Field(default=5, alias="OTP_EXPIRY_MINUTES")
    max_upload_mb: int = Field(default=25, alias="MAX_UPLOAD_MB")
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "doc", "txt", "jpg", "jpeg", "png"],
        alias="ALLOWED_EXTENSIONS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", populate_by_name=True)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
