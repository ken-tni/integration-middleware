from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from app.core.authentication import auth_manager
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.utils.logging import get_logger

logger = get_logger("api.auth")

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    adapter_name: str
    username: str
    password: str
    custom_headers: Optional[Dict[str, str]] = None


class LoginResponse(BaseModel):
    """Login response model"""
    status: str
    message: str
    adapter_name: str
    session_id: str


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate with an adapter system
    
    Logs in to the specified adapter using username and password.
    Returns a session ID for use in subsequent requests.
    """
    try:
        # Generate a simple user ID from request (in a real system, this would come from your auth system)
        client_host = request.client.host if request.client else "unknown"
        # This is a simplistic approach - in production you would have proper user authentication
        user_id = f"user-{client_host}"
        
        # Authenticate with the adapter
        session = await auth_manager.authenticate(
            user_id=user_id,
            adapter_name=login_data.adapter_name,
            username=login_data.username,
            password=login_data.password,
            custom_headers=login_data.custom_headers
        )
        
        return LoginResponse(
            status="success",
            message=f"Successfully authenticated with {login_data.adapter_name}",
            adapter_name=login_data.adapter_name,
            session_id=user_id  # In a real system, you would use a secure session token
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}"
        )
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/logout/{adapter_name}")
async def logout(
    adapter_name: str,
    request: Request,
    session_id: Optional[str] = Header(None)
):
    """Logout from an adapter system"""
    try:
        # Use provided session ID or generate from request
        user_id = session_id
        if not user_id:
            client_host = request.client.host if request.client else "unknown"
            user_id = f"user-{client_host}"
        
        success = auth_manager.invalidate_session(user_id, adapter_name)
        
        if success:
            return {"status": "success", "message": f"Successfully logged out from {adapter_name}"}
        else:
            return {"status": "warning", "message": f"No active session found for {adapter_name}"}
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        ) 