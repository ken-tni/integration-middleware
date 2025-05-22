import httpx
from typing import Dict, Any, Optional
from app.core.exceptions import (
    AdapterError,
    AuthenticationError,
    EntityNotFoundError,
    RateLimitError,
)
from app.utils.logging import get_logger
from app.utils.retry import adapter_retry

logger = get_logger("cloud_erp_client")

class CloudERPClient:
    """HTTP client for CloudERP API with token-based authentication."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the CloudERP client with API key authentication.
        
        Args:
            config: Configuration dictionary with API credentials
        """
        config = config or {}
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        
        if not self.base_url:
            raise ValueError("CloudERP base URL is required")
        if not self.api_key or not self.api_secret:
            raise ValueError("CloudERP API credentials are required")
        
        # Remove trailing slash from base_url if present
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        # Create HTTP client with token authentication headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}:{self.api_secret}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,  # 30 seconds timeout
        )
        
        logger.debug(f"CloudERP client initialized with base URL: {self.base_url}")
        
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
        """Make an HTTP request to the CloudERP API.
        
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
                    message="Authentication failed with CloudERP API",
                    source_system="CloudERP",
                )
            
            if response.status_code == 404:
                entity_type = path.strip("/").split("/")[-1]
                entity_id = params.get("id", "") if params else ""
                raise EntityNotFoundError(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    source_system="CloudERP",
                )
            
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    message="CloudERP API rate limit exceeded",
                    source_system="CloudERP",
                    retry_after=int(retry_after),
                )
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            json_response = response.json()
            logger.debug(f"Raw API response: {json_response}")
            
            # Return JSON response as is
            return json_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise AdapterError(
                message=f"CloudERP API error: {e.response.status_code} - {e.response.text}",
                source_system="CloudERP",
                original_error=e,
            )
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise AdapterError(
                message=f"CloudERP API request failed: {str(e)}",
                source_system="CloudERP",
                original_error=e,
            )

    async def get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a GET request to the CloudERP API."""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the CloudERP API."""
        return await self._request("POST", path, json_data=data)

    async def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the CloudERP API."""
        return await self._request("PUT", path, json_data=data)

    async def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request to the CloudERP API."""
        return await self._request("DELETE", path) 