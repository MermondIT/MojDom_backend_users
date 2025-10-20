"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "MòjDom API"
    debug: bool
    
    # Database
    database_url: str
    api_port: int
    
    access_token_expire_minutes: int = 30
    
    # Public API token
    public_token: str
    
    sendgrid_api_key: str

    # External Listings API
    external_listings_url: str
    external_listings_endpoint: str
    external_listings_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra="allow"



# Global settings instance
settings = Settings()
