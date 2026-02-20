from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Get the backend directory (parent of src)
backend_dir = Path(__file__).parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    
    CLOUDINARY_CLOUD_NAME:str
    CLOUDINARY_API_KEY:str
    CLOUDINARY_SECRET:str
    
    model_config = SettingsConfigDict(
        env_file=str(backend_dir / ".env"),
        env_file_encoding='utf-8'
    )

settings = Settings()
