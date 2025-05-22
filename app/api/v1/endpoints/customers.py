from typing import Optional, Dict
from fastapi import Query, Request, Depends
from app.schemas.customer import Customer, CustomerResponse, CustomerList
from app.api.v1.endpoints.base_endpoint import BaseEndpoint
from app.config.settings import get_setting
from app.api.v1.dependencies import get_adapter_with_auth

# Get adapter preference for this entity type (allows overriding the global default)
CUSTOMER_ADAPTER = get_setting("CUSTOMER_ADAPTER", None)

# Create a base endpoint for customers
customer_endpoint = BaseEndpoint(
    entity_type="customer",
    request_model=Customer,
    response_model=CustomerResponse,
    list_model=CustomerList,
    tag="customers",
    path_param_name="customer_id",
    default_adapter=CUSTOMER_ADAPTER,  # Entity-specific default adapter
)

# Get the router from the endpoint
router = customer_endpoint.router

# Override the list endpoint to add custom filtering
@router.get("", response_model=CustomerList)
async def list_customers(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    adapter_name: Optional[str] = Query(None, description="Adapter to use (defaults to system default)"),
    adapter = Depends(get_adapter_with_auth),
):
    """
    List customers with optional filtering.
    
    This endpoint retrieves a list of customers from the source system and returns them in the standardized format.
    
    - For token-based adapters: No additional authentication needed
    - For password-based adapters: Include X-Session-ID header with valid session ID
    """
    # Build filter dict
    filters = {}
    if name is not None:
        filters["name"] = name
    if status_filter is not None:
        filters["status"] = status_filter
    
    # Use the adapter dependency and don't call list_entities_with_filters directly 
    # (which would create another dependency chain)
    result = await adapter.search("customer", filters, page, page_size)
    return result 