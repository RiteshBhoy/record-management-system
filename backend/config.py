"""Application configuration.

This module contains separate configuration classes for local development
and production deployment.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# Load local environment variables from backend/.env.
#
# On a production hosting platform, environment variables are normally
# configured in the provider dashboard instead of a physical .env file.
load_dotenv(BASE_DIR / ".env")

# def get_database_url() -> str | None:
#     """Return a SQLAlchemy-compatible database connection URL.

#     SQLite is handled by the development configuration when no database
#     URL is provided.

#     PostgreSQL URLs are normalized to explicitly use the Psycopg 3
#     SQLAlchemy driver.
#     """

#     database_url = os.getenv("DATABASE_URL")

#     if not database_url:
#         return None

#     if database_url.startswith("postgres://"):
#         database_url = database_url.replace(
#             "postgres://",
#             "postgresql+psycopg://",
#             1,
#         )

#     elif database_url.startswith("postgresql://"):
#         database_url = database_url.replace(
#             "postgresql://",
#             "postgresql+psycopg://",
#             1,
#         )

#     return database_url

def get_database_url() -> str | None:
    """Return a SQLAlchemy-compatible database connection URL.

    PostgreSQL URLs are normalized to explicitly use the Psycopg 3
    SQLAlchemy driver.

    Relative SQLite URLs are converted to an absolute path inside the
    backend directory so Flask CLI and application startup use the same
    database file.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return None

    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("sqlite:///"):
        sqlite_path = database_url.removeprefix(
            "sqlite:///"
        )

        database_path = Path(sqlite_path)

        if not database_path.is_absolute():
            database_path = (
                BASE_DIR / database_path
            ).resolve()

        return f"sqlite:///{database_path.as_posix()}"

    return database_url

class BaseConfig:
    """Shared configuration used by all application environments."""

    SECRET_KEY = os.getenv("SECRET_KEY")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    AUTO_CREATE_TABLES = (
        os.getenv(
            "AUTO_CREATE_TABLES",
            "false",
        ).lower()
        == "true"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(
            os.getenv(
                "JWT_ACCESS_TOKEN_EXPIRES_HOURS",
                "8",
            )
        )
    )

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    JSON_SORT_KEYS = False

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5000,http://localhost:5000",
    ).split(",")


class DevelopmentConfig(BaseConfig):
    """Configuration used while running the project locally."""

    DEBUG = True

    ENV = "development"

    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     "DATABASE_URL",
    #     f"sqlite:///{BASE_DIR / 'database.db'}",
    # )
    SQLALCHEMY_DATABASE_URI = (
    get_database_url()
    or f"sqlite:///{BASE_DIR / 'database.db'}"
    )


class ProductionConfig(BaseConfig):
    """Configuration used when the application is deployed."""

    DEBUG = False

    ENV = "production"

    # SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = get_database_url()

    @classmethod
    def validate(cls) -> None:
        """Validate mandatory production environment variables."""

        required_variables = {
            "SECRET_KEY": cls.SECRET_KEY,
            "JWT_SECRET_KEY": cls.JWT_SECRET_KEY,
            "DATABASE_URL": cls.SQLALCHEMY_DATABASE_URI,
        }

        missing_variables = [
            variable_name
            for variable_name, variable_value in required_variables.items()
            if not variable_value
        ]

        if missing_variables:
            missing_names = ", ".join(missing_variables)

            raise RuntimeError(
                "Missing required production environment variables: "
                f"{missing_names}"
            )

        if len(cls.SECRET_KEY) < 32:
            raise RuntimeError(
                "SECRET_KEY must contain at least 32 characters "
                "in production."
            )

        if len(cls.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY must contain at least 32 characters "
                "in production."
            )


def get_config():
    """Return the correct configuration class for the current environment."""

    environment = os.getenv(
        "FLASK_ENV",
        "development",
    ).lower()

    if environment == "production":
        ProductionConfig.validate()

        return ProductionConfig

    return DevelopmentConfig