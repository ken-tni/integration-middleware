from typing import Dict, Any, Optional
from fastapi import APIRouter, Path, Query, HTTPException
from app.core.adapter_factory import adapter_factory
from app.schemas.customer import Customer, CustomerResponse, CustomerList
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger("api.customers")


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str = Path(..., description="Customer ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Get a customer by ID.
    
    This endpoint retrieves a customer from the source system and returns it in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        customer = await adapter.get_by_id("customer", customer_id)
        return customer
    except EntityNotFoundError as e:
        logger.info(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error retrieving customer: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("", response_model=CustomerList)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    List customers with optional filtering.
    
    This endpoint retrieves a list of customers from the source system and returns them in the standardized format.
    """
    try:
        # Build filters
        filters = {}
        if name:
            filters["name"] = name
        if status_filter:
            filters["status"] = status_filter
        
        adapter = await adapter_factory.get_adapter(adapter_name)
        result = await adapter.search("customer", filters, page, page_size)
        return result
    except AdapterError as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer: Customer,
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Create a new customer.
    
    This endpoint creates a new customer in the source system and returns the created customer in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        created_customer = await adapter.create("customer", customer.dict())
        return created_customer
    except AdapterError as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer: Customer,
    customer_id: str = Path(..., description="Customer ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Update a customer.
    
    This endpoint updates a customer in the source system and returns the updated customer in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        updated_customer = await adapter.update("customer", customer_id, customer.dict())
        return updated_customer
    except EntityNotFoundError as e:
        logger.info(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str = Path(..., description="Customer ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Delete a customer.
    
    This endpoint deletes a customer from the source system.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        await adapter.delete("customer", customer_id)
        return None
    except EntityNotFoundError as e:
        logger.info(f"Customer not found: {customer_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=502, detail=str(e)) 