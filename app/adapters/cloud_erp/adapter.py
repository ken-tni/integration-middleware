from typing import Dict, Any, Optional
from app.utils.logging import get_logger
from app.core.adapter import BaseAdapter
from app.adapters.cloud_erp.client import CloudERPClient
from app.core.exceptions import EntityNotFoundError, AdapterError


logger = get_logger("erp_next_adapter")


class CloudERPAdapter(BaseAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None, client: Optional[CloudERPClient] = None):
        self.config = config or {}
        self.endpoints = self.config.get("endpoints", {})
        self.client = client or CloudERPClient(config=self.config)
        self._entity_type_map = self.config.get("entity_map", {})

    async def connect(self) -> None:
        pass  # Implement if needed

    async def get_by_id(self, entity_type: str, entity_id: str):
        erp_entity_type = self._entity_type_map.get(entity_type, entity_type)
        path = self.endpoints["get_by_id"].format(entity_type=erp_entity_type, entity_id=entity_id)
        return await self.client.get(path)

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
            
            # Convert filters to ERPNext format
            erp_filters = self._convert_filters_to_erp(entity_type, filters)
            
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
            
            # # Get total count
            # count_response = await self.client.get(
            #     f"/api/resource/{erp_entity_type}/count",
            #     params={"filters": erp_filters},
            # )
            # total = count_response.get("count", 0)
            total = 0
            # Convert to standardized format
            items = response.get("data", [])
            if entity_type == "customer":
                customers = [self._convert_customer(item) for item in items]
                return {"total": total, "customers": customers}
            elif entity_type == "product":
                products = [self._convert_product(item) for item in items]
                return {"total": total, "products": products}
            elif entity_type == "quotation":
                quotations = [self._convert_quotation(item) for item in items]
                return {"total": total, "quotations": quotations}
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
        
        except Exception as e:
            logger.error(f"Error searching for {entity_type}: {e}")
            raise AdapterError(
                message=f"Failed to search for {entity_type}",
                source_system="ERPNext",
                original_error=e,
            )

    async def create(self, entity_type: str, data: Dict[str, Any]):
        erp_entity_type = self._entity_type_map.get(entity_type, entity_type)
        path = self.endpoints["create"].format(entity_type=erp_entity_type)
        return await self.client.post(path, data=data)

    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]):
        erp_entity_type = self._entity_type_map.get(entity_type, entity_type)
        path = self.endpoints["update"].format(entity_type=erp_entity_type, entity_id=entity_id)
        return await self.client.put(path, data=data)

    async def delete(self, entity_type: str, entity_id: str):
        erp_entity_type = self._entity_type_map.get(entity_type, entity_type)
        path = self.endpoints["delete"].format(entity_type=erp_entity_type, entity_id=entity_id)
        return await self.client.delete(path) 
    
    def _get_erp_entity_type(self, entity_type: str) -> str:
        """Get the ERPNext entity type for a standardized entity type."""
        return self._entity_type_map.get(entity_type, entity_type.capitalize()) 