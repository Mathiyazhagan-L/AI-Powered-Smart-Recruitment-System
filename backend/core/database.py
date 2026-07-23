import os
from urllib.parse import quote_plus
from pydantic import Extra
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "recruitment_db"

    # Optional tuning
    SQLALCHEMY_ECHO: bool = False
    POOL_PRE_PING: bool = True
    FUTURE: bool = True
    CHARSET: str = "utf8mb4"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": Extra.ignore,
    }


settings = Settings()


# Build a safe URL (quote password or other special chars)
password = quote_plus(settings.DB_PASSWORD)
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)


engine = create_engine(
    DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=settings.POOL_PRE_PING,
    future=settings.FUTURE,
    connect_args={"charset": settings.CHARSET},
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    return engine