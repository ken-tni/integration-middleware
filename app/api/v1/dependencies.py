from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request, Header, status
from app.core.adapter_factory import adapter_factory
from app.core.authentication import auth_manager
from app.core.adapter import BaseAdapter
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.utils.logging import get_logger

logger = get_logger("api.dependencies")


async def get_adapter_with_auth(
    request: Request,
    adapter_name: str = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    x_adapter_name: Optional[str] = Header(None, alias="X-Adapter-Name")
) -> BaseAdapter:
    """
    Get an adapter instance with appropriate authentication.
    
    Token-based adapters are handled directly by the adapter client implementation.
    Password-based adapters require session authentication.
    """
    # Resolve adapter name from various sources
    actual_adapter_name = _resolve_adapter_name(request, adapter_name, x_adapter_name)
    
    # Validate we have an adapter name
    if not actual_adapter_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adapter name required (in path, parameter, or header)"
        )
    
    try:
        # Get adapter config
        config = adapter_factory.get_adapter_config(actual_adapter_name)
        auth_method = config.get("auth_method", "token")
        
        # For password-based auth, get session info
        if auth_method == "password":
            # Get session ID from headers or request state
            session_id = x_session_id
            if not session_id and hasattr(request.state, "session_id"):
                session_id = request.state.session_id
                
            if not session_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for this adapter (X-Session-ID header missing)"
                )
            
            # Get authentication details from request state or auth manager
            auth_headers = None
            auth_cookies = None
            
            if hasattr(request.state, "auth_headers") and hasattr(request.state, "auth_cookies"):
                auth_headers = request.state.auth_headers
                auth_cookies = request.state.auth_cookies
            else:
                # Try to get from auth manager
                try:
                    auth_headers = auth_manager.get_auth_headers(session_id, actual_adapter_name)
                    auth_cookies = auth_manager.get_auth_cookies(session_id, actual_adapter_name)
                except AuthenticationError:
                    # Will be handled by the except block below
                    raise
            
            # Get adapter with session credentials
            return await adapter_factory.get_adapter(
                name=actual_adapter_name,
                session_id=session_id,
                auth_headers=auth_headers,
                auth_cookies=auth_cookies
            )
        
        # For token-based auth, use standard adapter
        # The adapter client will handle authentication with API keys from config
        return await adapter_factory.get_adapter(actual_adapter_name)
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration error: {str(e)}"
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Error getting adapter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


def _resolve_adapter_name(request: Request, explicit_name: str = None, header_name: str = None) -> Optional[str]:
    """Resolve adapter name from different sources."""
    # Priority 1: Explicit parameter
    if explicit_name:
        return explicit_name
    
    # Priority 2: Header
    if header_name:
        return header_name
        
    # Priority 3: Request state (set by middleware)
    if hasattr(request.state, "adapter_name"):
        return request.state.adapter_name
        
    # Priority 4: Query parameter
    query_params = request.query_params
    if "adapter_name" in query_params:
        return query_params["adapter_name"]
    
    # Priority 5: Path parameter format: /api/v1/{adapter_name}/...
    if request.url.path.startswith("/api/v1/"):
        path_parts = request.url.path.split("/")
        if len(path_parts) > 3:
            # Check if this is a valid adapter name
            potential_name = path_parts[3]
            try:
                if potential_name in adapter_factory._configs:
                    return potential_name
            except:
                pass
                
    return None


# Legacy function for backward compatibility
async def get_session_adapter(
    request: Request,
    adapter_name: str = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    x_adapter_name: Optional[str] = Header(None, alias="X-Adapter-Name")
) -> BaseAdapter:
    """Legacy function - redirects to get_adapter_with_auth"""
    return await get_adapter_with_auth(request, adapter_name, x_session_id, x_adapter_name) 