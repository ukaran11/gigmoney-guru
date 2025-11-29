"""
GigMoney Guru - Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/gigmoney"
    
    # OpenAI
    openai_api_key: str = ""
    
    # JWT
    jwt_secret: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # App
    app_name: str = "GigMoney Guru"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
