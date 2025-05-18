from typing import Dict, Any, Optional
from fastapi import APIRouter, Path, Query, HTTPException
from app.core.adapter_factory import adapter_factory
from app.schemas.quotation import Quotation, QuotationResponse, QuotationList
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.utils.logging import get_logger
from datetime import date

router = APIRouter()
logger = get_logger("api.quotations")


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(
    quotation_id: str = Path(..., description="Quotation ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Get a quotation by ID.
    
    This endpoint retrieves a quotation from the source system and returns it in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        quotation = await adapter.get_by_id("quotation", quotation_id)
        return quotation
    except EntityNotFoundError as e:
        logger.info(f"Quotation not found: {quotation_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error retrieving quotation: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("", response_model=QuotationList)
async def list_quotations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Filter by transaction date (from)"),
    to_date: Optional[date] = Query(None, description="Filter by transaction date (to)"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    List quotations with optional filtering.
    
    This endpoint retrieves a list of quotations from the source system and returns them in the standardized format.
    """
    try:
        # Build filters
        filters = {}
        if customer_name:
            filters["customer_name"] = customer_name
        if status_filter:
            filters["status"] = status_filter
        if from_date and to_date:
            filters["transaction_date_range"] = (from_date, to_date)
        elif from_date:
            filters["transaction_date_gte"] = from_date
        elif to_date:
            filters["transaction_date_lte"] = to_date
        
        adapter = await adapter_factory.get_adapter(adapter_name)
        result = await adapter.search("quotation", filters, page, page_size)
        return result
    except AdapterError as e:
        logger.error(f"Error listing quotations: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("", response_model=QuotationResponse, status_code=201)
async def create_quotation(
    quotation: Quotation,
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Create a new quotation.
    
    This endpoint creates a new quotation in the source system and returns the created quotation in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        created_quotation = await adapter.create("quotation", quotation.dict())
        return created_quotation
    except AdapterError as e:
        logger.error(f"Error creating quotation: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation: Quotation,
    quotation_id: str = Path(..., description="Quotation ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Update a quotation.
    
    This endpoint updates a quotation in the source system and returns the updated quotation in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        updated_quotation = await adapter.update("quotation", quotation_id, quotation.dict())
        return updated_quotation
    except EntityNotFoundError as e:
        logger.info(f"Quotation not found: {quotation_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error updating quotation: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{quotation_id}", status_code=204)
async def delete_quotation(
    quotation_id: str = Path(..., description="Quotation ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Delete a quotation.
    
    This endpoint deletes a quotation from the source system.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        await adapter.delete("quotation", quotation_id)
        return None
    except EntityNotFoundError as e:
        logger.info(f"Quotation not found: {quotation_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error deleting quotation: {e}")
        raise HTTPException(status_code=502, detail=str(e)) 