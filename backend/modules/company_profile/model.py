from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey
)

import datetime

from core.base import Base

class CompanyProfile(Base):

    __tablename__ = "company_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    company_name = Column(
        String(255),
        nullable=False
    )

    company_email = Column(
        String(255),
        nullable=False,
        unique=True
    )

    company_phone = Column(
        String(20),
        nullable=True
    )

    website = Column(
        String(255),
        nullable=True
    )

    company_code = Column(
        String(50),
        unique=True,
        index=True,
        nullable=True
    )

    industry = Column(
        String(255),
        nullable=True
    )

    company_size = Column(
        String(100),
        nullable=True
    )

    location = Column(
        String(255),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    linkedin_url = Column(
        String(500),
        nullable=True
    )

    logo_url = Column(
        String(500),
        nullable=True
    )

    gst_number = Column(
        String(50),
        nullable=True
    )

    is_email_verified = Column(
        Boolean,
        default=False
    )

    verification_status = Column(
        String(50),
        default="Pending"
    )

    verified_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )

    @property
    def website_url(self):
        return self.website

    @website_url.setter
    def website_url(self, value):
        self.website = value

    @property
    def company_description(self):
        return self.description

    @company_description.setter
    def company_description(self, value):
        self.description = value