from typing import Optional, Dict
from fastapi import Query, Request, Depends
from app.schemas.quotation import Quotation, QuotationResponse, QuotationList
from app.api.v1.endpoints.base_endpoint import BaseEndpoint
from app.config.settings import get_setting
from app.api.v1.dependencies import get_adapter_with_auth

# Get adapter preference for this entity type (allows overriding the global default)
QUOTATION_ADAPTER = get_setting("QUOTATION_ADAPTER", None)

# Create a base endpoint for quotations
quotation_endpoint = BaseEndpoint(
    entity_type="quotation",
    request_model=Quotation,
    response_model=QuotationResponse,
    list_model=QuotationList,
    tag="quotations",
    path_param_name="quotation_id",
    default_adapter=QUOTATION_ADAPTER,  # Entity-specific default adapter
)

# Get the router from the endpoint
router = quotation_endpoint.router

# Override the list endpoint to add custom filtering
@router.get("", response_model=QuotationList)
async def list_quotations(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[str] = Query(None, description="Filter by quotation date (from)"),
    to_date: Optional[str] = Query(None, description="Filter by quotation date (to)"),
    adapter_name: Optional[str] = Query(None, description="Adapter to use (defaults to system default)"),
    adapter = Depends(get_adapter_with_auth),
):
    """
    List quotations with optional filtering.
    
    This endpoint retrieves a list of quotations from the source system and returns them in the standardized format.
    """
    # Build filter dict
    filters = {}
    if customer_id is not None:
        filters["customer_id"] = customer_id
    if status_filter is not None:
        filters["status"] = status_filter
    if from_date is not None:
        filters["quotation_date_from"] = from_date
    if to_date is not None:
        filters["quotation_date_to"] = to_date
    
    # Use the adapter dependency and don't call list_entities_with_filters directly 
    # (which would create another dependency chain)
    result = await adapter.search("quotation", filters, page, page_size)
    return result 