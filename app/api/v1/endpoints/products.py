from typing import Dict, Any, Optional
from fastapi import APIRouter, Path, Query, HTTPException
from app.core.adapter_factory import adapter_factory
from app.schemas.product import Product, ProductResponse, ProductList
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger("api.products")


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(..., description="Product ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Get a product by ID.
    
    This endpoint retrieves a product from the source system and returns it in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        product = await adapter.get_by_id("product", product_id)
        return product
    except EntityNotFoundError as e:
        logger.info(f"Product not found: {product_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error retrieving product: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.get("", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name"),
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    List products with optional filtering.
    
    This endpoint retrieves a list of products from the source system and returns them in the standardized format.
    """
    try:
        # Build filters
        filters = {}
        if name:
            filters["name"] = name
        if sku:
            filters["sku"] = sku
        if category:
            filters["category"] = category
        if is_active is not None:
            filters["is_active"] = is_active
        
        adapter = await adapter_factory.get_adapter(adapter_name)
        result = await adapter.search("product", filters, page, page_size)
        return result
    except AdapterError as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: Product,
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Create a new product.
    
    This endpoint creates a new product in the source system and returns the created product in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        created_product = await adapter.create("product", product.dict())
        return created_product
    except AdapterError as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product: Product,
    product_id: str = Path(..., description="Product ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Update a product.
    
    This endpoint updates a product in the source system and returns the updated product in the standardized format.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        updated_product = await adapter.update("product", product_id, product.dict())
        return updated_product
    except EntityNotFoundError as e:
        logger.info(f"Product not found: {product_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str = Path(..., description="Product ID"),
    adapter_name: str = Query("erp_next", description="Adapter to use"),
):
    """
    Delete a product.
    
    This endpoint deletes a product from the source system.
    """
    try:
        adapter = await adapter_factory.get_adapter(adapter_name)
        await adapter.delete("product", product_id)
        return None
    except EntityNotFoundError as e:
        logger.info(f"Product not found: {product_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except AdapterError as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=502, detail=str(e)) 