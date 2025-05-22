from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.authentication import auth_manager
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.core.adapter_factory import adapter_factory
from app.utils.logging import get_logger

logger = get_logger("auth_middleware")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for handling adapter authentication"""
    
    async def dispatch(self, request: Request, call_next):
        """Process each request to apply authentication"""
        # Skip authentication for auth endpoints and docs
        if request.url.path.startswith("/api/v1/auth/") or request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            return await call_next(request)
        
        # Check if this is an adapter endpoint
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)
        
        # Get adapter name from header or path
        adapter_name = self._get_adapter_name_from_request(request)
        
        # If no adapter specified, continue without auth
        if not adapter_name:
            return await call_next(request)
        
        try:
            # Store adapter name in request state for later use
            request.state.adapter_name = adapter_name
            
            # Get adapter config
            config = adapter_factory.get_adapter_config(adapter_name)
            auth_method = config.get("auth_method", "token")
            
            # Only handle password-based authentication in middleware
            if auth_method == "password":
                # Get session ID from header
                session_id = request.headers.get("X-Session-ID")
                
                # If no session ID, authentication is required
                if not session_id:
                    logger.warning(f"Authentication required for {adapter_name} (password auth)")
                    return Response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content="Authentication required for password-based adapter",
                        media_type="text/plain"
                    )
                
                # Check if session exists and is valid
                session = auth_manager.get_session(session_id, adapter_name)
                if not session or not session.active:
                    logger.warning(f"No active session for {adapter_name}")
                    return Response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content="No active session or session expired",
                        media_type="text/plain"
                    )
                
                # Attach session information to request state
                request.state.session_id = session_id
                request.state.auth_headers = auth_manager.get_auth_headers(session_id, adapter_name)
                request.state.auth_cookies = auth_manager.get_auth_cookies(session_id, adapter_name)
            
            # Process the request - token-based auth is handled by the adapter client itself
            return await call_next(request)
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {str(e)}")
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Configuration error: {str(e)}",
                media_type="text/plain"
            )
        except Exception as e:
            logger.error(f"Error in auth middleware: {str(e)}")
            return Response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content="Internal server error",
                media_type="text/plain"
            )
            
    def _get_adapter_name_from_request(self, request: Request) -> Optional[str]:
        """Extract adapter name from request header, query param, or path."""
        # Try header first
        adapter_name = request.headers.get("X-Adapter-Name")
        if adapter_name:
            return adapter_name
            
        # Try query parameter
        query_params = request.query_params
        if "adapter_name" in query_params:
            return query_params["adapter_name"]
            
        # Try path parameter format: /api/v1/{adapter_name}/...
        path_parts = request.url.path.split("/")
        if len(path_parts) > 3:
            # Don't treat entity types as adapter names
            potential_name = path_parts[3]
            # Check if this is a valid adapter name
            try:
                if potential_name in adapter_factory._configs:
                    return potential_name
            except:
                pass
                
        return None 