import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    """Application settings."""
    # Application settings
    APP_NAME: str = "system-b-middleware"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # System A (ERPNext) settings
    SYSTEM_A_BASE_URL: str = os.getenv("SYSTEM_A_BASE_URL", "")
    SYSTEM_A_API_KEY: str = os.getenv("SYSTEM_A_API_KEY", "")
    SYSTEM_A_API_SECRET: str = os.getenv("SYSTEM_A_API_SECRET", "")
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Create settings instance
settings = Settings() 