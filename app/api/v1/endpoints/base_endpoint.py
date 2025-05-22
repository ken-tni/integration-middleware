from typing import Dict, Any, Optional, Type, List, Callable, TypeVar, Generic
from fastapi import APIRouter, Path, Query, HTTPException, Depends, Request
from pydantic import BaseModel
import os
from app.core.adapter_factory import adapter_factory
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.utils.logging import get_logger
from app.config.settings import DEFAULT_ADAPTER
from app.api.v1.dependencies import get_adapter_with_auth

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=BaseModel)
L = TypeVar('L', bound=BaseModel)

logger = get_logger("api.base_endpoint")


class BaseEndpoint(Generic[T, R, L]):
    """Base endpoint factory that generates CRUD operations for any entity type.
    
    This class reduces code duplication by providing a common implementation
    for standard CRUD operations that can be customized per entity type.
    """
    
    def __init__(
        self,
        entity_type: str,
        request_model: Type[T],
        response_model: Type[R],
        list_model: Type[L],
        tag: str,
        path_param_name: str,
        default_adapter: str = None,
    ):
        """Initialize the base endpoint.
        
        Args:
            entity_type: Type of entity (e.g., "customer", "product", "invoice")
            request_model: Pydantic model for request body
            response_model: Pydantic model for response
            list_model: Pydantic model for list response
            tag: API tag for documentation
            path_param_name: Name of the path parameter (e.g., "customer_id")
            default_adapter: Default adapter to use (overrides env variable)
        """
        self.entity_type = entity_type
        self.request_model = request_model
        self.response_model = response_model
        self.list_model = list_model
        self.tag = tag
        self.path_param_name = path_param_name
        self.default_adapter = default_adapter or DEFAULT_ADAPTER
        self.router = APIRouter(tags=[tag])
        
        # Set up the logger
        self.logger = get_logger(f"api.{entity_type}s")
        logger.info(f"Initialized {entity_type} endpoint with default adapter: {self.default_adapter}")
        
        # Register the standard endpoints
        self._register_endpoints()
    
    def _register_endpoints(self) -> None:
        """Register all standard CRUD endpoints."""
        # GET by ID
        self.router.add_api_route(
            "/{entity_id}", 
            self.get_entity,
            methods=["GET"],
            response_model=self.response_model,
            summary=f"Get {self.entity_type}",
            description=f"Get a {self.entity_type} by ID",
        )
        
        # List entities - Don't register it here, let each entity override it
        # with their own implementation
        
        # Create entity
        self.router.add_api_route(
            "", 
            self.create_entity,
            methods=["POST"],
            response_model=self.response_model,
            status_code=201,
            summary=f"Create {self.entity_type}",
            description=f"Create a new {self.entity_type}",
        )
        
        # Update entity
        self.router.add_api_route(
            "/{entity_id}", 
            self.update_entity,
            methods=["PUT"],
            response_model=self.response_model,
            summary=f"Update {self.entity_type}",
            description=f"Update an existing {self.entity_type}",
        )
        
        # Delete entity
        self.router.add_api_route(
            "/{entity_id}", 
            self.delete_entity,
            methods=["DELETE"],
            status_code=204,
            summary=f"Delete {self.entity_type}",
            description=f"Delete a {self.entity_type}",
        )
    
    async def get_entity(
        self,
        request: Request,
        entity_id: str,
        adapter_name: Optional[str] = None,
        adapter = Depends(get_adapter_with_auth),
    ):
        """Get an entity by ID."""
        try:
            # Use the adapter provided by the dependency, which handles
            # both token and password authentication methods
            adapter_to_use = adapter_name or self.default_adapter
            self.logger.debug(f"Using adapter: {adapter_to_use} to get {self.entity_type} with ID: {entity_id}")
            
            entity = await adapter.get_by_id(self.entity_type, entity_id)
            return entity
        except EntityNotFoundError as e:
            self.logger.info(f"{self.entity_type.capitalize()} not found: {entity_id}")
            raise HTTPException(status_code=404, detail=str(e))
        except AdapterError as e:
            self.logger.error(f"Error retrieving {self.entity_type}: {e}")
            raise HTTPException(status_code=502, detail=str(e))
    
    async def list_entities_with_filters(
        self,
        request: Request,
        page: int = 1,
        page_size: int = 100,
        adapter_name: Optional[str] = None,
        filters: Dict[str, Any] = None,
        adapter = Depends(get_adapter_with_auth),
    ):
        """List entities with custom filters."""
        try:
            # Use provided filters or empty dict
            filters = filters or {}
            
            adapter_to_use = adapter_name or self.default_adapter
            self.logger.debug(f"Using adapter: {adapter_to_use} to list {self.entity_type}s")
            
            result = await adapter.search(self.entity_type, filters, page, page_size)
            return result
        except AdapterError as e:
            self.logger.error(f"Error listing {self.entity_type}s: {e}")
            raise HTTPException(status_code=502, detail=str(e))
    
    async def create_entity(
        self,
        request: Request,
        entity: T,
        adapter_name: Optional[str] = None,
        adapter = Depends(get_adapter_with_auth),
    ):
        """Create a new entity."""
        try:
            adapter_to_use = adapter_name or self.default_adapter
            self.logger.debug(f"Using adapter: {adapter_to_use} to create {self.entity_type}")
            
            created_entity = await adapter.create(self.entity_type, entity.dict())
            return created_entity
        except AdapterError as e:
            self.logger.error(f"Error creating {self.entity_type}: {e}")
            raise HTTPException(status_code=502, detail=str(e))
    
    async def update_entity(
        self,
        request: Request,
        entity_id: str,
        entity: T,
        adapter_name: Optional[str] = None,
        adapter = Depends(get_adapter_with_auth),
    ):
        """Update an entity."""
        try:
            adapter_to_use = adapter_name or self.default_adapter
            self.logger.debug(f"Using adapter: {adapter_to_use} to update {self.entity_type} with ID: {entity_id}")
            
            updated_entity = await adapter.update(self.entity_type, entity_id, entity.dict())
            return updated_entity
        except EntityNotFoundError as e:
            self.logger.info(f"{self.entity_type.capitalize()} not found: {entity_id}")
            raise HTTPException(status_code=404, detail=str(e))
        except AdapterError as e:
            self.logger.error(f"Error updating {self.entity_type}: {e}")
            raise HTTPException(status_code=502, detail=str(e))
    
    async def delete_entity(
        self,
        request: Request,
        entity_id: str,
        adapter_name: Optional[str] = None,
        adapter = Depends(get_adapter_with_auth),
    ):
        """Delete an entity."""
        try:
            adapter_to_use = adapter_name or self.default_adapter
            self.logger.debug(f"Using adapter: {adapter_to_use} to delete {self.entity_type} with ID: {entity_id}")
            
            await adapter.delete(self.entity_type, entity_id)
            return None
        except EntityNotFoundError as e:
            self.logger.info(f"{self.entity_type.capitalize()} not found: {entity_id}")
            raise HTTPException(status_code=404, detail=str(e))
        except AdapterError as e:
            self.logger.error(f"Error deleting {self.entity_type}: {e}")
            raise HTTPException(status_code=502, detail=str(e))

    def add_custom_endpoint(
        self,
        path: str,
        endpoint_func: Callable,
        methods: List[str],
        **kwargs,
    ):
        """Add a custom endpoint to the router."""
        self.router.add_api_route(
            path,
            endpoint_func,
            methods=methods,
            **kwargs,
        ) 