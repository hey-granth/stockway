from os import getenv
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY: str = getenv("SECRET_KEY")
    DEBUG: bool = getenv("DEBUG", "False")

    DATABASE_URL: str = getenv("DATABASE_URL")
    DB_USER: str = getenv("DB_USER")
    DB_PASSWORD: str = getenv("DB_PASSWORD")
    DB_HOST: str = getenv("DB_HOST", "localhost")
    DB_PORT: str = getenv("DB_PORT", "5432")
    DB_NAME: str = getenv("DB_NAME")
    FAST2SMS_API_KEY: str = getenv("FAST2SMS_API_KEY")

    # Supabase Configuration
    SUPABASE_URL: str = getenv("SUPABASE_URL")
    SUPABASE_KEY: str = getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: str = getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_JWT_SECRET: str = getenv("SUPABASE_JWT_SECRET")

    # Optional: Supabase Managed Postgres
    SUPABASE_DB_HOST: str = getenv("SUPABASE_DB_HOST")
    SUPABASE_DB_PORT: str = getenv("SUPABASE_DB_PORT", "5432")
    SUPABASE_DB_NAME: str = getenv("SUPABASE_DB_NAME", "postgres")
    SUPABASE_DB_USER: str = getenv("SUPABASE_DB_USER", "postgres")
    SUPABASE_DB_PASSWORD: str = getenv("SUPABASE_DB_PASSWORD")
