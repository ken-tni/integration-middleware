from datetime import datetime, date
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from app.adapters.erp_next.client import ERPNextClient
from app.core.adapter import BaseAdapter
from app.core.conversions.converter_factory import converter_factory
from app.core.exceptions import EntityNotFoundError, AdapterError, AuthenticationError
from app.schemas.customer import Customer
from app.schemas.product import Product
from app.schemas.quotation import Quotation, QuotationItem
from app.schemas.base import MetadataSchema
from app.utils.logging import get_logger

T = TypeVar('T', Customer, Product, Quotation)
logger = get_logger("erp_next_adapter")


class ERPNextAdapter(BaseAdapter[T]):
    """Adapter for ERPNext API with support for both token and session authentication."""
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        client: Optional[ERPNextClient] = None,
        session_id: Optional[str] = None,
        auth_headers: Optional[Dict[str, str]] = None,
        auth_cookies: Optional[Dict[str, str]] = None
    ):
        """Initialize the ERPNext adapter with either token or session authentication.
        
        Args:
            config: Adapter configuration dictionary
            client: Optional ERPNext client instance
            session_id: Session ID for session-based authentication
            auth_headers: Authentication headers for session-based authentication
            auth_cookies: Authentication cookies for session-based authentication
        """
        self.config = config or {}
        self.endpoints = self.config.get("endpoints", {})
        self.auth_method = self.config.get("auth_method", "token")
        self.adapter_name = "erp_next"
        
        # Create client if not provided
        if not client:
            self.client = ERPNextClient(
                config=self.config,
                session_id=session_id,
                auth_headers=auth_headers,
                auth_cookies=auth_cookies
            )
        else:
            self.client = client
            
        # Entity type mapping
        self._entity_type_map = self.config.get("entity_map", {
            "customer": "Customer",
            "product": "Item",
            "quotation": "Quotation",
            "invoice": "Sales Invoice",
        })
    
    async def connect(self) -> None:
        """Initialize connection to ERPNext."""
        # Nothing to do here as the client is already initialized
        logger.debug(f"ERPNext adapter connected using {self.auth_method} authentication")
    
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
            logger.warning("authenticate() called but adapter is not in password auth mode")
            raise AuthenticationError(
                message="Cannot authenticate: adapter is not in password auth mode",
                source_system="ERPNext"
            )
        
        # Delegate to client's authenticate method
        return await self.client.authenticate(username, password)
    
    async def get_by_id(self, entity_type: str, entity_id: str) -> T:
        """Get a single entity by ID from ERPNext.
        
        Args:
            entity_type: The type of entity to retrieve (e.g., "customer", "product")
            entity_id: The ID of the entity in ERPNext
            
        Returns:
            The standardized entity object
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Get data from ERPNext
            path = self.endpoints["get_by_id"].format(entity_type=erp_entity_type, entity_id=entity_id)
            # Request all fields
            params = {
                "fields": '["*"]'  # Request all fields
            }
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw {entity_type} data from ERPNext: {response}")
            
            # Use centralized converter to convert to standardized format
            converter = converter_factory.get_converter(entity_type)
            return converter.external_to_standard("erp_next", response.get("data", {}))
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to get {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def search(
        self, entity_type: str, filters: Dict[str, Any], page: int = 1, page_size: int = 100
    ) -> Dict[str, Any]:
        """Search for entities in ERPNext.
        
        Args:
            entity_type: The type of entity to search for
            filters: Dict of filter parameters
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing total count and list of entities
            
        Raises:
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Calculate pagination parameters
            limit_start = (page - 1) * page_size
            limit_page_length = page_size
            
            # Convert filters to ERPNext format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            erp_filters = converter.convert_filters("erp_next", entity_type, filters)
            
            # Get data from ERPNext
            path = self.endpoints["search"].format(entity_type=erp_entity_type)
            params = {
                "filters": erp_filters,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
                "fields": '["*"]'  # Request all fields
            }
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw {entity_type} search results from ERPNext: {response}")
            
            # Get total count and items from the response
            # The response structure might be different based on the ERPNext version
            items = response.get("items", [])
            if not items and "data" in response:
                items = response.get("data", [])
                
            # If no items found and data is a dict, check if it has 'items' inside
            if not items and isinstance(response.get("data"), dict):
                items = response.get("data", {}).get("items", [])
                
            # Get total or use length of items
            total = response.get("total", len(items))
            
            # Convert to standardized format
            converted_items = []
            
            for item in items:
                converted_items.append(
                    converter.external_to_standard("erp_next", item)
                )
            
            # Return results in the expected format, matching the exact field name expected by the schema
            if entity_type == "customer":
                return {"total": total, "customers": converted_items}
            elif entity_type == "product":
                return {"total": total, "products": converted_items}
            elif entity_type == "quotation":
                return {"total": total, "quotations": converted_items}
            elif entity_type == "invoice":
                return {"total": total, "invoices": converted_items}
            else:
                # Use a dynamic key for other entity types
                entity_list_key = f"{entity_type}s"
                return {"total": total, entity_list_key: converted_items}
        
        except Exception as e:
            logger.error(f"Error searching for {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to search for {entity_type}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> T:
        """Create a new entity in ERPNext.
        
        Args:
            entity_type: The type of entity to create
            data: The data for the new entity
            
        Returns:
            The created entity in standardized format
            
        Raises:
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to ERPNext format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            erp_data = converter.standard_to_external("erp_next", data)
            
            # Create in ERPNext
            path = self.endpoints["create"].format(entity_type=erp_entity_type)
            response = await self.client.post(path, data=erp_data)
            
            # Get the created entity
            created_id = response.get("data", {}).get("name")
            if not created_id:
                raise AdapterError(
                    message=f"Failed to get ID of created {entity_type}",
                    source_system="ERPNext",
                )
            
            return await self.get_by_id(entity_type, created_id)
        
        except Exception as e:
            logger.error(f"Error creating {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to create {entity_type}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> T:
        """Update an existing entity in ERPNext.
        
        Args:
            entity_type: The type of entity to update
            entity_id: The ID of the entity to update
            data: The fields to update
            
        Returns:
            The updated entity in standardized format
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to ERPNext format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            erp_data = converter.standard_to_external("erp_next", data)
            
            # Update in ERPNext
            path = self.endpoints["update"].format(entity_type=erp_entity_type, entity_id=entity_id)
            await self.client.put(path, data=erp_data)
            
            # Get the updated entity
            return await self.get_by_id(entity_type, entity_id)
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to update {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity in ERPNext.
        
        Args:
            entity_type: The type of entity to delete
            entity_id: The ID of the entity to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with ERPNext
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Delete in ERPNext
            path = self.endpoints["delete"].format(entity_type=erp_entity_type, entity_id=entity_id)
            await self.client.delete(path)
            return True
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to delete {entity_type} with ID {entity_id}",
                source_system="ERPNext",
                original_error=e,
            )
    
    async def close(self):
        """Close the connection to ERPNext."""
        if self.client:
            await self.client.close()
    
    def _get_erp_entity_type(self, entity_type: str) -> str:
        """Get the ERPNext entity type for a standardized entity type."""
        return self._entity_type_map.get(entity_type, entity_type.capitalize()) 