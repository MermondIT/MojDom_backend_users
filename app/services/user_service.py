"""
User service for business logic
"""

from typing import Optional
from uuid import UUID
from fastapi import Request
from app.exceptions.custom_exceptions import UnauthorizedException
from app.config import settings

print(settings.public_token)
class UserService:
    """Service for user authentication and authorization"""
    
    def __init__(self, request: Request):
        self.request = request
        self._user_guid: Optional[UUID] = None
        self._public_token: Optional[UUID] = None
    
    @property
    def user_guid(self) -> UUID:
        """Get user GUID, raise exception if not authorized"""
        if self._user_guid is None:
            raise UnauthorizedException("User not authenticated")
        return self._user_guid
    
    @property
    def public_token(self) -> Optional[UUID]:
        """Get public token if present"""
        return self._public_token
    
    def _extract_tokens(self):
        """Extract tokens from request headers"""
        # Extract ACCESS-TOKEN
        access_token = self.request.headers.get("ACCESS-TOKEN")
        if access_token:
            try:
                self._user_guid = UUID(access_token)
            except ValueError:
                pass
        
        # Extract PUBLIC-TOKEN
        public_token = self.request.headers.get("PUBLIC-TOKEN")
        if public_token:
            try:
                self._public_token = UUID(public_token)
            except ValueError:
                pass
    
    def throw_if_unauthorized(self):
        """Throw exception if user is not authorized"""
        self._extract_tokens()
        if self._user_guid is None:
            raise UnauthorizedException("Access token required")
    
    def throw_if_public_unauthorized(self):
        """Throw exception if public token is not valid"""
        self._extract_tokens()
        if self._public_token is None or str(self._public_token) != settings.public_token:
            raise UnauthorizedException("Invalid public token")


class PublicUserService:
    """Service for public API authentication"""
    
    def __init__(self, request: Request):
        self.request = request
        self._user_guid: Optional[UUID] = None
        self._public_token: Optional[UUID] = None
    
    @property
    def user_guid(self) -> Optional[UUID]:
        """Get user GUID if present"""
        return self._user_guid
    
    def _extract_tokens(self):
        """Extract tokens from request headers"""
        # Extract ACCESS-TOKEN
        access_token = self.request.headers.get("ACCESS-TOKEN")
        if access_token:
            try:
                self._user_guid = UUID(access_token)
            except ValueError:
                pass
        
        # Extract PUBLIC-TOKEN
        public_token = self.request.headers.get("PUBLIC-TOKEN")
        if public_token:
            try:
                self._public_token = UUID(public_token)
            except ValueError:
                pass
    
    def throw_if_unauthorized(self):
        """Throw exception if public token is not valid"""
        self._extract_tokens()
        if self._public_token is None or str(self._public_token) != settings.public_token:
            raise UnauthorizedException("Invalid public token")
