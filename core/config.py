import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Django settings
    SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-default-key-change-this")
    DEBUG = os.getenv("DEBUG", "True") == "True"

    # Database settings
    DB_NAME = os.getenv("DB_NAME", "backend_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")

    # Test Database URL (only used during Django test runs)
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

    # Supabase settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

    # Optional: Supabase Managed Postgres
    SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST")
    SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")
    SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME")
    SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER")
    SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

    # CORS settings
    CORS_ALLOWED_ORIGINS = (
        os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if os.getenv("CORS_ALLOWED_ORIGINS")
        else []
    )

    # Redis settings for caching and live tracking
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
