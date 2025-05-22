import json
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel
from app.utils.logging import get_logger
from app.core.exceptions import AuthenticationError, ConfigurationError

logger = get_logger("auth_manager")

# Path to adapter configs
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config/adapters'))

class AdapterSession(BaseModel):
    """Model for adapter session data"""
    adapter_name: str
    session_id: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    expires_at: Optional[datetime] = None
    active: bool = False


class AuthManager:
    """Manages authentication sessions for adapter systems"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, AdapterSession]] = {}  # user_id -> {adapter_name -> session}
        
    async def authenticate(self, user_id: str, adapter_name: str, username: str, password: str, 
                           custom_headers: Optional[Dict[str, str]] = None) -> AdapterSession:
        """Authenticate with an adapter system and store the session"""
        from app.core.adapter_factory import adapter_factory
        
        try:
            # Get adapter config to check auth method
            adapter_config = adapter_factory.get_adapter_config(adapter_name)
            auth_method = adapter_config.get("auth_method", "token")
            
            if auth_method != "password":
                raise ConfigurationError(f"Adapter {adapter_name} does not use password authentication")
            
            # Create a new adapter instance
            # For an adapter that has both token and password auth, we create it here
            # without a session and then call authenticate
            adapter = await adapter_factory.get_adapter(adapter_name)
            
            # Call the adapter's authenticate method directly
            auth_result = await adapter.authenticate(username, password)
            
            # Extract authentication details from response
            if not auth_result:
                raise AuthenticationError(
                    message=f"Authentication failed with {adapter_name}",
                    source_system=adapter_name
                )
            
            # Create session object
            session = AdapterSession(
                adapter_name=adapter_name,
                session_id=auth_result.get("session_id"),
                cookies=auth_result.get("auth_cookies", {}),
                headers=auth_result.get("auth_headers", {}),
                expires_at=datetime.now() + timedelta(hours=1),  # Default 1 hour expiration
                active=True
            )
            
            # Store session
            if user_id not in self._sessions:
                self._sessions[user_id] = {}
                
            self._sessions[user_id][adapter_name] = session
            logger.info(f"Created authentication session for user {user_id} with adapter {adapter_name}")
            
            return session
                
        except ConfigurationError as e:
            logger.error(f"Configuration error for {adapter_name}: {e}")
            raise
        except AuthenticationError as e:
            logger.error(f"Authentication failed for {adapter_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during authentication for {adapter_name}: {e}")
            raise AuthenticationError(
                message=f"Authentication error for {adapter_name}: {str(e)}",
                source_system=adapter_name
            )
    
    def get_session(self, user_id: str, adapter_name: str) -> Optional[AdapterSession]:
        """Get an existing adapter session for a user"""
        if user_id in self._sessions and adapter_name in self._sessions[user_id]:
            session = self._sessions[user_id][adapter_name]
            
            # Check if session has expired
            if session.expires_at and session.expires_at < datetime.now():
                session.active = False
                logger.debug(f"Session expired for user {user_id} with adapter {adapter_name}")
                
            return session
        return None
    
    def get_auth_headers(self, user_id: str, adapter_name: str) -> Dict[str, str]:
        """Get authentication headers for an adapter session"""
        session = self.get_session(user_id, adapter_name)
        if not session or not session.active:
            raise AuthenticationError(
                message=f"No active session for adapter {adapter_name}",
                source_system=adapter_name
            )
            
        return session.headers or {}
    
    def get_auth_cookies(self, user_id: str, adapter_name: str) -> Dict[str, str]:
        """Get authentication cookies for an adapter session"""
        session = self.get_session(user_id, adapter_name)
        if not session or not session.active:
            raise AuthenticationError(
                message=f"No active session for adapter {adapter_name}",
                source_system=adapter_name
            )
            
        return session.cookies or {}
    
    def invalidate_session(self, user_id: str, adapter_name: str) -> bool:
        """Invalidate a session for a user and adapter"""
        if user_id in self._sessions and adapter_name in self._sessions[user_id]:
            self._sessions[user_id][adapter_name].active = False
            return True
        return False


# Create singleton instance
auth_manager = AuthManager() 