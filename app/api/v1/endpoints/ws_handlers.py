from typing import Dict, Any
from app.utils.logging import get_logger
from app.core.middleware.websocket_service import ws_endpoint
from app.core.adapter_factory import adapter_factory
from app.core.exceptions import AdapterError, EntityNotFoundError

logger = get_logger("api.ws_handlers")

@ws_endpoint(name="customers/list")
async def get_customers(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example WebSocket endpoint handler to get list of customers
    This would typically call your existing customer service logic
    """
    # Normally you would call your existing service layer
    # from app.services.customer_service import get_customers_list
    # return await get_customers_list(**params)
    
    # For demonstration, returning mock data
    return {
        "customers": [
            {"id": 1, "name": "Customer 1"},
            {"id": 2, "name": "Customer 2"},
            {"id": 3, "name": "Customer 3"}
        ]
    }

@ws_endpoint(name="products/search")
async def search_products(params: Dict[str, Any]) -> Dict[str, Any]:
    """Example WebSocket endpoint handler to search products"""
    query = params.get("query", "")
    
    # Normally call your existing product service
    # For demonstration, returning mock data
    return {
        "query": query,
        "products": [
            {"id": 101, "name": f"Product matching '{query}'", "price": 99.99},
            {"id": 102, "name": f"Another product with '{query}'", "price": 149.99}
        ]
    }

@ws_endpoint(name="quotations/create")
async def create_quotation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Example WebSocket endpoint handler to create a quotation"""
    customer_id = params.get("customer_id")
    items = params.get("items", [])
    
    if not customer_id:
        raise ValueError("customer_id is required")
    
    if not items:
        raise ValueError("At least one item is required")
    
    # Normally call your quotation service to create a new quotation
    # For demonstration, returning mock response
    return {
        "quotation_id": 12345,
        "customer_id": customer_id,
        "status": "created",
        "message": f"Created quotation with {len(items)} items"
    } 

@ws_endpoint(name="entity/get")
async def get_entity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket endpoint handler to get entity data from a specific adapter
    
    Required parameters:
    - adapter_name: The name of the adapter to use (e.g. "erp_next", "cloud_erp")
    - entity_type: The type of entity to retrieve (e.g. "customer", "product", "quotation")
    - entity_id: The ID of the entity to retrieve
    
    Optional parameters:
    - session_id: Session ID for session-based authentication
    """
    # Extract required parameters
    adapter_name = params.get("adapter_name")
    entity_type = params.get("entity_type")
    entity_id = params.get("entity_id")
    
    # Validate required parameters
    if not adapter_name:
        raise ValueError("adapter_name is required")
    if not entity_type:
        raise ValueError("entity_type is required")
    if not entity_id:
        raise ValueError("entity_id is required")
    
    try:
        # Get any session parameters if provided
        session_id = params.get("session_id")
        auth_headers = params.get("auth_headers")
        auth_cookies = params.get("auth_cookies")
        
        # Get the adapter instance
        adapter = await adapter_factory.get_adapter(
            adapter_name, 
            session_id=session_id,
            auth_headers=auth_headers, 
            auth_cookies=auth_cookies
        )
        
        # Get the entity data
        entity = await adapter.get_by_id(entity_type, entity_id)
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": entity
        }
    
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found: {entity_type} with ID {entity_id} from {adapter_name}")
        return {
            "status": "error",
            "error_type": "entity_not_found",
            "message": str(e)
        }
    except AdapterError as e:
        logger.error(f"Adapter error when getting {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "adapter_error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when getting {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e)
        }

@ws_endpoint(name="entity/search")
async def search_entities(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket endpoint handler to search for entities from a specific adapter
    
    Required parameters:
    - adapter_name: The name of the adapter to use (e.g. "erp_next", "cloud_erp")
    - entity_type: The type of entity to search for (e.g. "customer", "product", "quotation")
    
    Optional parameters:
    - filters: Dictionary of filter criteria
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 100)
    - session_id: Session ID for session-based authentication
    """
    # Extract required parameters
    adapter_name = params.get("adapter_name")
    entity_type = params.get("entity_type")
    
    # Validate required parameters
    if not adapter_name:
        raise ValueError("adapter_name is required")
    if not entity_type:
        raise ValueError("entity_type is required")
    
    # Extract optional parameters
    filters = params.get("filters", {})
    page = params.get("page", 1)
    page_size = params.get("page_size", 100)
    
    try:
        # Get any session parameters if provided
        session_id = params.get("session_id")
        auth_headers = params.get("auth_headers")
        auth_cookies = params.get("auth_cookies")
        
        # Get the adapter instance
        adapter = await adapter_factory.get_adapter(
            adapter_name, 
            session_id=session_id,
            auth_headers=auth_headers, 
            auth_cookies=auth_cookies
        )
        
        # Search for entities
        result = await adapter.search(entity_type, filters, page, page_size)
        
        return {
            "entity_type": entity_type,
            "page": page,
            "page_size": page_size,
            "data": result
        }
    
    except AdapterError as e:
        logger.error(f"Adapter error when searching for {entity_type}: {e}")
        return {
            "status": "error",
            "error_type": "adapter_error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when searching for {entity_type}: {e}")
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e)
        }

@ws_endpoint(name="entity/create")
async def create_entity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket endpoint handler to create an entity using a specific adapter
    
    Required parameters:
    - adapter_name: The name of the adapter to use (e.g. "erp_next", "cloud_erp")
    - entity_type: The type of entity to create (e.g. "customer", "product", "quotation")
    - data: The entity data to create
    
    Optional parameters:
    - session_id: Session ID for session-based authentication
    """
    # Extract required parameters
    adapter_name = params.get("adapter_name")
    entity_type = params.get("entity_type")
    entity_data = params.get("data")
    
    # Validate required parameters
    if not adapter_name:
        raise ValueError("adapter_name is required")
    if not entity_type:
        raise ValueError("entity_type is required")
    if not entity_data:
        raise ValueError("data is required")
    
    try:
        # Get any session parameters if provided
        session_id = params.get("session_id")
        auth_headers = params.get("auth_headers")
        auth_cookies = params.get("auth_cookies")
        
        # Get the adapter instance
        adapter = await adapter_factory.get_adapter(
            adapter_name, 
            session_id=session_id,
            auth_headers=auth_headers, 
            auth_cookies=auth_cookies
        )
        
        # Create the entity
        created_entity = await adapter.create(entity_type, entity_data)
        
        return {
            "entity_type": entity_type,
            "status": "created",
            "data": created_entity
        }
    
    except AdapterError as e:
        logger.error(f"Adapter error when creating {entity_type}: {e}")
        return {
            "status": "error",
            "error_type": "adapter_error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when creating {entity_type}: {e}")
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e)
        }

@ws_endpoint(name="entity/update")
async def update_entity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket endpoint handler to update an entity using a specific adapter
    
    Required parameters:
    - adapter_name: The name of the adapter to use (e.g. "erp_next", "cloud_erp")
    - entity_type: The type of entity to update (e.g. "customer", "product", "quotation")
    - entity_id: The ID of the entity to update
    - data: The updated entity data
    
    Optional parameters:
    - session_id: Session ID for session-based authentication
    """
    # Extract required parameters
    adapter_name = params.get("adapter_name")
    entity_type = params.get("entity_type")
    entity_id = params.get("entity_id")
    entity_data = params.get("data")
    
    # Validate required parameters
    if not adapter_name:
        raise ValueError("adapter_name is required")
    if not entity_type:
        raise ValueError("entity_type is required")
    if not entity_id:
        raise ValueError("entity_id is required")
    if not entity_data:
        raise ValueError("data is required")
    
    try:
        # Get any session parameters if provided
        session_id = params.get("session_id")
        auth_headers = params.get("auth_headers")
        auth_cookies = params.get("auth_cookies")
        
        # Get the adapter instance
        adapter = await adapter_factory.get_adapter(
            adapter_name, 
            session_id=session_id,
            auth_headers=auth_headers, 
            auth_cookies=auth_cookies
        )
        
        # Update the entity
        updated_entity = await adapter.update(entity_type, entity_id, entity_data)
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "updated",
            "data": updated_entity
        }
    
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found for update: {entity_type} with ID {entity_id} from {adapter_name}")
        return {
            "status": "error",
            "error_type": "entity_not_found",
            "message": str(e)
        }
    except AdapterError as e:
        logger.error(f"Adapter error when updating {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "adapter_error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when updating {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e)
        } 

@ws_endpoint(name="entity/delete")
async def delete_entity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket endpoint handler to delete an entity using a specific adapter
    
    Required parameters:
    - adapter_name: The name of the adapter to use (e.g. "erp_next", "cloud_erp")
    - entity_type: The type of entity to delete (e.g. "customer", "product", "quotation")
    - entity_id: The ID of the entity to delete
    
    Optional parameters:
    - session_id: Session ID for session-based authentication
    """
    # Extract required parameters
    adapter_name = params.get("adapter_name")
    entity_type = params.get("entity_type")
    entity_id = params.get("entity_id")
    
    # Validate required parameters
    if not adapter_name:
        raise ValueError("adapter_name is required")
    if not entity_type:
        raise ValueError("entity_type is required")
    if not entity_id:
        raise ValueError("entity_id is required")
    
    try:
        # Get any session parameters if provided
        session_id = params.get("session_id")
        auth_headers = params.get("auth_headers")
        auth_cookies = params.get("auth_cookies")
        
        # Get the adapter instance
        adapter = await adapter_factory.get_adapter(
            adapter_name, 
            session_id=session_id,
            auth_headers=auth_headers, 
            auth_cookies=auth_cookies
        )
        
        # Delete the entity
        success = await adapter.delete(entity_type, entity_id)
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "deleted" if success else "failed"
        }
    
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found for deletion: {entity_type} with ID {entity_id} from {adapter_name}")
        return {
            "status": "error",
            "error_type": "entity_not_found",
            "message": str(e)
        }
    except AdapterError as e:
        logger.error(f"Adapter error when deleting {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "adapter_error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error when deleting {entity_type} with ID {entity_id}: {e}")
        return {
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(e)
        } 