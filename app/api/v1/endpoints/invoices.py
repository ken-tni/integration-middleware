from typing import Optional, Dict
from fastapi import Query, Request, Depends
from app.schemas.invoice import Invoice, InvoiceResponse, InvoiceList
from app.api.v1.endpoints.base_endpoint import BaseEndpoint
from app.config.settings import get_setting
from app.api.v1.dependencies import get_adapter_with_auth

# Get adapter preference for this entity type (allows overriding the global default)
INVOICE_ADAPTER = get_setting("INVOICE_ADAPTER", None)

# Create a base endpoint for invoices
invoice_endpoint = BaseEndpoint(
    entity_type="invoice",
    request_model=Invoice,
    response_model=InvoiceResponse,
    list_model=InvoiceList,
    tag="invoices",
    path_param_name="invoice_id",
    default_adapter=INVOICE_ADAPTER,  # Entity-specific default adapter
)

# Get the router from the endpoint
router = invoice_endpoint.router

# Override the list endpoint to add custom filtering
@router.get("", response_model=InvoiceList)
async def list_invoices(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[str] = Query(None, description="Filter by invoice date (from)"),
    to_date: Optional[str] = Query(None, description="Filter by invoice date (to)"),
    adapter_name: Optional[str] = Query(None, description="Adapter to use (defaults to system default)"),
    adapter = Depends(get_adapter_with_auth),
):
    """
    List invoices with optional filtering.
    
    This endpoint retrieves a list of invoices from the source system and returns them in the standardized format.
    """
    # Build filter dict
    filters = {}
    if customer_id is not None:
        filters["customer_id"] = customer_id
    if status_filter is not None:
        filters["status"] = status_filter
    if from_date is not None:
        filters["invoice_date_from"] = from_date
    if to_date is not None:
        filters["invoice_date_to"] = to_date
        
    # Use the adapter dependency and don't call list_entities_with_filters directly 
    # (which would create another dependency chain)
    result = await adapter.search("invoice", filters, page, page_size)
    return result 