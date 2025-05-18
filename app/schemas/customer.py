from typing import Optional, List
from pydantic import Field, BaseModel
from app.schemas.base import BaseSchema, ContactInfo, MetadataSchema


class Customer(BaseSchema):
    """Standardized customer schema."""
    name: str = Field(..., description="Customer name")
    customer_type: str = Field(..., description="Customer type (Individual, Company, etc.)")
    contact_info: ContactInfo = Field(..., description="Contact information")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    status: str = Field(..., description="Customer status (Active, Inactive, etc.)")
    credit_limit: Optional[float] = Field(None, description="Credit limit")
    notes: Optional[str] = Field(None, description="Additional notes")
    # Additional ERPNext fields
    owner: Optional[str] = Field(None, description="Owner of the document")
    modified_by: Optional[str] = Field(None, description="User who last modified the document")
    docstatus: Optional[int] = Field(None, description="Document status (0=Draft, 1=Submitted, 2=Cancelled)")
    naming_series: Optional[str] = Field(None, description="Naming series for the document")
    salutation: Optional[str] = Field(None, description="Salutation (Mr, Mrs, Ms, etc.)")
    customer_group: Optional[str] = Field(None, description="Customer group")
    territory: Optional[str] = Field(None, description="Territory")
    gender: Optional[str] = Field(None, description="Gender")
    lead_name: Optional[str] = Field(None, description="Lead name")
    opportunity_name: Optional[str] = Field(None, description="Opportunity name")
    prospect_name: Optional[str] = Field(None, description="Prospect name")
    account_manager: Optional[str] = Field(None, description="Account manager")
    image: Optional[str] = Field(None, description="Customer image")
    mobile_no: Optional[str] = Field(None, description="Mobile number")
    email_id: Optional[str] = Field(None, description="Email ID")
    website: Optional[str] = Field(None, description="Website")
    language: Optional[str] = Field(None, description="Language preference")
    market_segment: Optional[str] = Field(None, description="Market segment")
    default_currency: Optional[str] = Field(None, description="Default currency")
    metadata: MetadataSchema = Field(..., description="Source system metadata")


class CustomerResponse(BaseSchema):
    """Customer response schema for API endpoints."""
    name: str
    customer_type: str
    contact_info: ContactInfo
    tax_id: Optional[str] = None
    status: str
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    # Additional ERPNext fields
    owner: Optional[str] = None
    modified_by: Optional[str] = None
    docstatus: Optional[int] = None
    naming_series: Optional[str] = None
    salutation: Optional[str] = None
    customer_group: Optional[str] = None
    territory: Optional[str] = None
    gender: Optional[str] = None
    lead_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    prospect_name: Optional[str] = None
    account_manager: Optional[str] = None
    image: Optional[str] = None
    mobile_no: Optional[str] = None
    email_id: Optional[str] = None
    website: Optional[str] = None
    language: Optional[str] = None
    market_segment: Optional[str] = None
    default_currency: Optional[str] = None


class CustomerList(BaseModel):
    """List of customers response schema."""
    total: int = Field(..., description="Total number of customers")
    customers: List[CustomerResponse] = Field(..., description="List of customers") 