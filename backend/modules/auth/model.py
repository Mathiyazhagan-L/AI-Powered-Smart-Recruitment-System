import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    text
)

from core.base import Base


# ==========================================
# USERS TABLE
# ==========================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    # Existing phone column — used as mobile_number in new registration flow
    phone = Column(
        String(20),
        unique=True,
        nullable=True,
        index=True
    )

    role = Column(
        String(20),
        nullable=False
    )

    full_name = Column(
        String(255),
        nullable=True
    )

    google_id = Column(
        String(255),
        nullable=True,
        unique=True
    )

    email_verified = Column(
        Boolean,
        default=False
    )

    phone_verified = Column(
        Boolean,
        default=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    # ── NEW COLUMNS (added via migrate_auth.py) ──────────────────────────────

    # Bcrypt-hashed password. NULL for Google-only accounts.
    password_hash = Column(
        String(255),
        nullable=True
    )

    # True once the user has verified their email OTP after registration.
    is_verified = Column(
        Boolean,
        default=False
    )

    # 'email' for normal sign-up, 'google' for OAuth accounts.
    auth_provider = Column(
        String(20),
        nullable=False,
        default='email'
    )

    # ─────────────────────────────────────────────────────────────────────────

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )


# ==========================================
# OTP TABLE
# ==========================================

class OTPRecord(Base):

    __tablename__ = "otp_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    target = Column(
        String(255),
        nullable=False,
        index=True
    )

    otp_code = Column(
        String(255),
        nullable=False
    )

    is_used = Column(
        Boolean,
        default=False
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )


# ==========================================
# REFRESH TOKEN TABLE
# ==========================================

class RefreshToken(Base):

    __tablename__ = "refresh_tokens"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    token = Column(
        String(1000),
        nullable=False
    )

    is_revoked = Column(
        Boolean,
        default=False
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )