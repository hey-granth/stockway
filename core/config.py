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
    SUPABASE_SERVICE_KEY = (
        os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_SERVICE_ROLE_KEY
    )
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

    # Upstash Redis settings for production (Celery broker/result backend)
    UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    # Render deployment settings
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

    @classmethod
    def get_redis_url(cls):
        """
        Get Redis connection URL based on environment.
        Returns Upstash Redis URL for production, local Redis for development.
        """
        # Production: Use Upstash Redis (REST API converted to Redis protocol URL)
        if cls.UPSTASH_REDIS_REST_URL and cls.UPSTASH_REDIS_REST_TOKEN:
            # Extract host and port from REST URL
            # Format: https://host:port
            import re
            match = re.search(r"https://([^:]+):?(\d+)?", cls.UPSTASH_REDIS_REST_URL)
            if match:
                host = match.group(1)
                port = match.group(2) or "6379"
                # Construct rediss:// URL with password (token)
                return f"rediss://:{cls.UPSTASH_REDIS_REST_TOKEN}@{host}:{port}"

        # Development: Use local Redis
        password_part = f":{cls.REDIS_PASSWORD}@" if cls.REDIS_PASSWORD else ""
        return f"redis://{password_part}{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
