import os
from typing import Optional # Import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() # Load .env file if present

class Settings(BaseSettings):
    PROJECT_NAME: str = "EKB Platform Backend"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ekb_db")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # 7 days

    # First Superuser
    FIRST_SUPERUSER_USERNAME: str = os.getenv("FIRST_SUPERUSER_USERNAME", "admin")
    FIRST_SUPERUSER_EMAIL: str = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")

    # OIDC Settings
    OIDC_CLIENT_ID: Optional[str] = os.getenv("OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET: Optional[str] = os.getenv("OIDC_CLIENT_SECRET")
    OIDC_DISCOVERY_URL: Optional[str] = os.getenv("OIDC_DISCOVERY_URL")
    # Default redirect URI, can be overridden if needed by specific flows
    OIDC_REDIRECT_URI: str = os.getenv("OIDC_REDIRECT_URI", f"{API_V1_STR}/auth/oidc/callback")


    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Type hint for Optional fields that are required for OIDC functionality
if not settings.OIDC_CLIENT_ID or not settings.OIDC_CLIENT_SECRET or not settings.OIDC_DISCOVERY_URL:
    print("Warning: OIDC environment variables (OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_DISCOVERY_URL) are not fully set. OIDC features may not work.")

