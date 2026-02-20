from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_SECRET: str
    
    model_config = SettingsConfigDict(
        env_file=[
            ".env",  # Current directory
            "backend/.env",  # If running from parent directory
            str(Path(__file__).parent.parent / ".env"),  # Relative to this file
        ],
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()
