from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import Field, BaseModel
from app.schemas.base import BaseSchema, ContactInfo, MetadataSchema


class InvoiceItem(BaseModel):
    """Schema for invoice line items."""
    product_id: str = Field(..., description="Product ID")
    description: str = Field(..., description="Item description")
    quantity: float = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    discount_percentage: Optional[float] = Field(0, description="Discount percentage")
    tax_percentage: Optional[float] = Field(0, description="Tax percentage")
    total_amount: float = Field(..., description="Total amount")


class Invoice(BaseSchema):
    """Standardized invoice schema."""
    number: str = Field(..., description="Invoice number")
    customer_id: str = Field(..., description="Customer ID")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Due date")
    status: str = Field(..., description="Invoice status (Draft, Paid, Overdue, etc.)")
    currency: str = Field(..., description="Currency code")
    subtotal: float = Field(..., description="Subtotal amount before tax")
    tax_total: float = Field(..., description="Total tax amount")
    discount_total: Optional[float] = Field(0, description="Total discount amount")
    grand_total: float = Field(..., description="Grand total amount")
    notes: Optional[str] = Field(None, description="Additional notes")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    items: List[InvoiceItem] = Field(..., description="Invoice line items")
    billing_address: Optional[ContactInfo] = Field(None, description="Billing address")
    shipping_address: Optional[ContactInfo] = Field(None, description="Shipping address")
    metadata: MetadataSchema = Field(..., description="Source system metadata")


class InvoiceResponse(BaseSchema):
    """Invoice response schema for API endpoints."""
    number: str
    customer_id: str
    invoice_date: date
    due_date: date
    status: str
    currency: str
    subtotal: float
    tax_total: float
    discount_total: Optional[float] = 0
    grand_total: float
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    items: List[InvoiceItem]
    billing_address: Optional[ContactInfo] = None
    shipping_address: Optional[ContactInfo] = None


class InvoiceList(BaseModel):
    """List of invoices response schema."""
    total: int = Field(..., description="Total number of invoices")
    invoices: List[InvoiceResponse] = Field(..., description="List of invoices") 