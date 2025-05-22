import httpx
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.core.exceptions import (
    AdapterError,
    AuthenticationError,
    EntityNotFoundError,
    RateLimitError,
)
from app.utils.logging import get_logger
from app.utils.retry import adapter_retry

logger = get_logger("erp_next_client")


class ERPNextClient:
    """HTTP client for ERPNext API."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        session_id: Optional[str] = None,
        auth_headers: Optional[Dict[str, str]] = None,
        auth_cookies: Optional[Dict[str, str]] = None,
    ):
        """Initialize the ERPNext client with either token or session authentication.
        
        Args:
            config: Adapter configuration dictionary
            base_url: The base URL of the ERPNext API
            api_key: The API key for token-based authentication
            api_secret: The API secret for token-based authentication
            session_id: Session ID for session-based authentication
            auth_headers: Custom auth headers for session-based authentication
            auth_cookies: Cookies for session-based authentication
        """
        config = config or {}
        self.base_url = base_url or config.get("base_url")
        
        if not self.base_url:
            raise ValueError("ERPNext base URL is required")
            
        # Remove trailing slash from base_url if present
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        self.auth_method = config.get("auth_method", "token")
        
        # Set up headers based on authentication method
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        cookies = {}
        
        # Handle token-based authentication
        if self.auth_method == "token":
            self.api_key = api_key or config.get("api_key")
            self.api_secret = api_secret or config.get("api_secret")
            
            if not self.api_key or not self.api_secret:
                raise ValueError("ERPNext API credentials are required for token auth")
                
            headers["Authorization"] = f"token {self.api_key}:{self.api_secret}"
            
        # Handle session-based authentication
        elif self.auth_method == "password":
            self.session_id = session_id
            
            # Add auth headers if provided
            if auth_headers:
                headers.update(auth_headers)
                
            # Add cookies if provided
            cookies = auth_cookies or {}
            
        # Create HTTP client with appropriate headers and cookies
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            cookies=cookies,
            timeout=30.0,  # 30 seconds timeout
        )
        
        logger.debug(f"ERPNext client initialized with base URL: {self.base_url} using auth method: {self.auth_method}")
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with ERPNext using username and password.
        
        Args:
            username: ERPNext username
            password: ERPNext password
            
        Returns:
            Authentication response with session details
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.auth_method != "password":
            logger.warning("authenticate() called but client is not in password auth mode")
            
        try:
            # Get the auth endpoint from config
            auth_endpoint = "/api/method/login"
            
            # Prepare login data
            login_data = {
                "usr": username,
                "pwd": password
            }
            
            # Make login request
            response = await self.client.post(auth_endpoint, json=login_data)
            
            if response.status_code != 200:
                raise AuthenticationError(
                    message=f"ERPNext authentication failed: {response.status_code} - {response.text}",
                    source_system="ERPNext"
                )
                
            # Extract session cookies and headers
            auth_cookies = dict(response.cookies)
            
            # In ERPNext, we typically need to extract the sid cookie
            if "sid" in auth_cookies:
                logger.info("Successfully authenticated with ERPNext")
                
                # Update client cookies
                self.client.cookies.update(auth_cookies)
                
                # Return auth details
                return {
                    "session_id": auth_cookies.get("sid"),
                    "auth_cookies": auth_cookies,
                    "user": username,
                    "success": True
                }
            else:
                raise AuthenticationError(
                    message="ERPNext authentication failed: No session cookie returned",
                    source_system="ERPNext"
                )
                
        except httpx.RequestError as e:
            logger.error(f"ERPNext authentication request failed: {e}")
            raise AuthenticationError(
                message=f"ERPNext authentication request failed: {str(e)}",
                source_system="ERPNext",
                original_error=e
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @adapter_retry
    async def _request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the ERPNext API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            EntityNotFoundError: If the requested entity doesn't exist
            RateLimitError: If rate limit is exceeded
            AdapterError: For other API errors
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"
        
        url = f"{self.base_url}{path}"
        logger.debug(f"{method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            
            # Handle common HTTP errors
            if response.status_code == 401:
                raise AuthenticationError(
                    message="Authentication failed with ERPNext API",
                    source_system="ERPNext",
                )
            
            if response.status_code == 404:
                entity_type = path.strip("/").split("/")[-2] if len(path.strip("/").split("/")) > 1 else path.strip("/")
                entity_id = path.strip("/").split("/")[-1] if len(path.strip("/").split("/")) > 1 else ""
                raise EntityNotFoundError(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    source_system="ERPNext",
                )
            
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    message="ERPNext API rate limit exceeded",
                    source_system="ERPNext",
                    retry_after=int(retry_after),
                )
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise AdapterError(
                message=f"ERPNext API error: {e.response.status_code} - {e.response.text}",
                source_system="ERPNext",
                original_error=e,
            )
        
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise AdapterError(
                message=f"ERPNext API request failed: {str(e)}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a GET request to the ERPNext API."""
        return await self._request("GET", path, params=params)
    
    async def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the ERPNext API."""
        return await self._request("POST", path, json_data=data)
    
    async def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the ERPNext API."""
        return await self._request("PUT", path, json_data=data)
    
    async def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request to the ERPNext API."""
        return await self._request("DELETE", path) 