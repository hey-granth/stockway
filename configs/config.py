from os import getenv
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = getenv("SECRET_KEY")
    DEBUG = getenv("DEBUG", "False")

    DATABASE_URL = getenv("DATABASE_URL")
    # Add other configuration variables as needed
    DB_USER = getenv("DB_USER")
    DB_PASSWORD = getenv("DB_PASSWORD")
    DB_HOST = getenv("DB_HOST", "localhost")
    DB_PORT = getenv("DB_PORT", "5432")
    DB_NAME = getenv("DB_NAME")
