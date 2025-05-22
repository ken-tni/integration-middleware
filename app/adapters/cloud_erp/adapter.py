from typing import Dict, Any, Optional
from app.utils.logging import get_logger
from app.core.adapter import BaseAdapter
from app.adapters.cloud_erp.client import CloudERPClient
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.core.conversions.converter_factory import converter_factory


logger = get_logger("cloud_erp_adapter")


class CloudERPAdapter(BaseAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None, client: Optional[CloudERPClient] = None):
        self.config = config or {}
        self.endpoints = self.config.get("endpoints", {})
        self.client = client or CloudERPClient(config=self.config)
        self._entity_type_map = self.config.get("entity_map", {})

    async def connect(self) -> None:
        pass  # Implement if needed

    async def get_by_id(self, entity_type: str, entity_id: str):
        """Get a single entity by ID from CloudERP.
        
        Args:
            entity_type: The type of entity to retrieve (e.g., "customer", "product")
            entity_id: The ID of the entity in CloudERP
            
        Returns:
            The standardized entity object
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with CloudERP
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Get data from CloudERP
            path = self.endpoints["get_by_id"].format(entity_type=erp_entity_type, entity_id=entity_id)
            # Request all fields
            params = {
                "fields": '["*"]'  # Request all fields
            }
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw {entity_type} data from CloudERP: {response}")
            
            # Use centralized converter to convert to standardized format
            converter = converter_factory.get_converter(entity_type)
            return converter.external_to_standard("cloud_erp", response.get("data", {}))
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to get {entity_type} with ID {entity_id}",
                source_system="CloudERP",
                original_error=e,
            )

    async def search(
        self, entity_type: str, filters: Dict[str, Any], page: int = 1, page_size: int = 100
    ) -> Dict[str, Any]:
        """Search for entities in CloudERP.
        
        Args:
            entity_type: The type of entity to search for
            filters: Dict of filter parameters
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing total count and list of entities
            
        Raises:
            AdapterError: If there's an error communicating with CloudERP
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Calculate pagination parameters
            limit_start = (page - 1) * page_size
            limit_page_length = page_size
            
            # Convert filters using the converter factory
            converter = converter_factory.get_converter(entity_type)
            erp_filters = converter.convert_filters("cloud_erp", entity_type, filters)
            
            # Get data from CloudERP
            path = self.endpoints["search"].format(entity_type=erp_entity_type)
            params = {
                "filters": erp_filters,
                "limit_start": limit_start,
                "limit_page_length": limit_page_length,
                "fields": '["*"]'  # Request all fields
            }
            logger.debug(f"Sending search request to CloudERP: {path} with params: {params}")
            response = await self.client.get(path, params=params)
            
            # Debug log the raw response
            logger.debug(f"Raw response from CloudERP API: {response}")
            
            # Check if response is directly from the API or already processed
            # The raw API response is the entire response object, not just data
            if isinstance(response, dict) and "data" in response:
                # Handle ERPNext-style response format
                api_data = response.get("data", [])
                total_count = 0  # Default if not available
                logger.debug(f"Using ERPNext-style response format with 'data' field")
            else:
                # Handle CloudERP response format
                api_data = response.get("items", [])
                total_count = response.get("total", 0)
                logger.debug(f"Using CloudERP response format with 'items' field")
            
            logger.debug(f"Extracted {len(api_data)} items from response")
            
            # Convert to standardized format
            converted_items = []
            for item in api_data:
                try:
                    converted_item = converter.external_to_standard("cloud_erp", item)
                    converted_items.append(converted_item)
                except Exception as e:
                    logger.error(f"Error converting item: {e}, item: {item}")
            
            logger.debug(f"Converted {len(converted_items)} items to standard format")
            
            # Build the response in the expected format
            result = {"total": total_count}
            
            # Set the appropriate key based on entity_type
            if entity_type == "customer":
                result["customers"] = converted_items
            elif entity_type == "product":
                result["products"] = converted_items
            elif entity_type == "quotation":
                result["quotations"] = converted_items
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            logger.debug(f"Returning transformed response: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error searching for {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to search for {entity_type}",
                source_system="CloudERP",
                original_error=e,
            )

    async def create(self, entity_type: str, data: Dict[str, Any]):
        """Create a new entity in CloudERP.
        
        Args:
            entity_type: The type of entity to create
            data: The data for the new entity
            
        Returns:
            The created entity in standardized format
            
        Raises:
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with CloudERP
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to CloudERP format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            erp_data = converter.standard_to_external("cloud_erp", data)
            
            # Create in CloudERP
            path = self.endpoints["create"].format(entity_type=erp_entity_type)
            response = await self.client.post(path, data=erp_data)
            
            # Get the created entity
            created_id = response.get("data", {}).get("name")
            if not created_id:
                raise AdapterError(
                    message=f"Failed to get ID of created {entity_type}",
                    source_system="CloudERP",
                )
            
            return await self.get_by_id(entity_type, created_id)
        
        except Exception as e:
            logger.error(f"Error creating {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to create {entity_type}",
                source_system="CloudERP",
                original_error=e,
            )

    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]):
        """Update an entity in CloudERP.
        
        Args:
            entity_type: The type of entity to update
            entity_id: The ID of the entity to update
            data: The updated data
            
        Returns:
            The updated entity in standardized format
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with CloudERP
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Convert to CloudERP format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            erp_data = converter.standard_to_external("cloud_erp", data)
            
            # Update in CloudERP
            path = self.endpoints["update"].format(entity_type=erp_entity_type, entity_id=entity_id)
            response = await self.client.put(path, data=erp_data)
            
            # Return the updated entity
            return await self.get_by_id(entity_type, entity_id)
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to update {entity_type} with ID {entity_id}",
                source_system="CloudERP",
                original_error=e,
            )

    async def delete(self, entity_type: str, entity_id: str):
        """Delete an entity in CloudERP.
        
        Args:
            entity_type: The type of entity to delete
            entity_id: The ID of the entity to delete
            
        Returns:
            True if the deletion was successful
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with CloudERP
        """
        erp_entity_type = self._get_erp_entity_type(entity_type)
        
        try:
            # Delete from CloudERP
            path = self.endpoints["delete"].format(entity_type=erp_entity_type, entity_id=entity_id)
            response = await self.client.delete(path)
            
            return True
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting {entity_type} with ID {entity_id}: {e}")
            raise AdapterError(
                message=f"Failed to delete {entity_type} with ID {entity_id}",
                source_system="CloudERP",
                original_error=e,
            )

    def _get_erp_entity_type(self, entity_type: str) -> str:
        """Get the CloudERP entity type for a standardized entity type."""
        return self._entity_type_map.get(entity_type, entity_type.capitalize())

    async def close(self):
        """Close connections and clean up resources."""
        if self.client:
            await self.client.close()
            logger.debug("CloudERP adapter closed") 