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
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        """Initialize the ERPNext client.
        
        Args:
            base_url: The base URL of the ERPNext API
            api_key: The API key for authentication
            api_secret: The API secret for authentication
        """
        self.base_url = base_url or settings.SYSTEM_A_BASE_URL
        self.api_key = api_key or settings.SYSTEM_A_API_KEY
        self.api_secret = api_secret or settings.SYSTEM_A_API_SECRET
        
        if not self.base_url:
            raise ValueError("ERPNext base URL is required")
        if not self.api_key or not self.api_secret:
            raise ValueError("ERPNext API credentials are required")
        
        # Remove trailing slash from base_url if present
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        
        # Create HTTP client with default headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"token {self.api_key}:{self.api_secret}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,  # 30 seconds timeout
        )
        
        logger.debug(f"ERPNext client initialized with base URL: {self.base_url}")
    
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
                entity_type = path.strip("/").split("/")[-1]
                entity_id = params.get("name", "") if params else ""
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