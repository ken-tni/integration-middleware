from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel
from app.schemas.base import BaseSchema, MetadataSchema


class ProductAttribute(BaseModel):
    """Product attribute schema."""
    name: str = Field(..., description="Attribute name")
    value: Any = Field(..., description="Attribute value")


class Product(BaseSchema):
    """Standardized product schema."""
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Stock Keeping Unit")
    description: str = Field(..., description="Product description")
    category: str = Field(..., description="Product category")
    price: float = Field(..., description="Product price")
    cost: Optional[float] = Field(None, description="Product cost")
    tax_rate: Optional[float] = Field(None, description="Tax rate")
    stock_quantity: int = Field(..., description="Available stock quantity")
    unit_of_measure: str = Field(..., description="Unit of measure")
    attributes: List[ProductAttribute] = Field(default_factory=list, description="Product attributes")
    is_active: bool = Field(..., description="Whether the product is active")
    metadata: MetadataSchema = Field(..., description="Source system metadata")


class ProductResponse(BaseSchema):
    """Product response schema for API endpoints."""
    name: str
    sku: str
    description: str
    category: str
    price: float
    stock_quantity: int
    unit_of_measure: str
    is_active: bool


class ProductList(BaseModel):
    """List of products response schema."""
    total: int = Field(..., description="Total number of products")
    products: List[ProductResponse] = Field(..., description="List of products") 