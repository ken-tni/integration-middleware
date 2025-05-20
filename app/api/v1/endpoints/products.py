from typing import Optional, Dict
from fastapi import Query
from app.schemas.product import Product, ProductResponse, ProductList
from app.api.v1.endpoints.base_endpoint import BaseEndpoint
from app.config.settings import get_setting

# Get adapter preference for this entity type (allows overriding the global default)
PRODUCT_ADAPTER = get_setting("PRODUCT_ADAPTER", None)

# Create a base endpoint for products
product_endpoint = BaseEndpoint(
    entity_type="product",
    request_model=Product,
    response_model=ProductResponse,
    list_model=ProductList,
    tag="products",
    path_param_name="product_id",
    default_adapter=PRODUCT_ADAPTER,  # Entity-specific default adapter
)

# Get the router from the endpoint
router = product_endpoint.router

# Override the list endpoint to add custom filtering
@router.get("", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    adapter_name: Optional[str] = Query(None, description="Adapter to use (defaults to system default)"),
):
    """
    List products with optional filtering.
    
    This endpoint retrieves a list of products from the source system and returns them in the standardized format.
    """
    # Build filter dict
    filters = {}
    if name is not None:
        filters["name"] = name
    if category is not None:
        filters["category"] = category
        
    return await product_endpoint.list_entities_with_filters(
        page=page,
        page_size=page_size,
        adapter_name=adapter_name,
        filters=filters,
    ) 