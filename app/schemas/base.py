from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic config."""
        from_attributes = True  # For ORM compatibility


class Address(BaseModel):
    """Standardized address schema."""
    street1: str = Field(..., description="Street address line 1")
    street2: Optional[str] = Field(None, description="Street address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")


class ContactInfo(BaseModel):
    """Standardized contact information schema."""
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    mobile: Optional[str] = Field(None, description="Mobile number")
    website: Optional[str] = Field(None, description="Website URL")
    address: Optional[Address] = Field(None, description="Physical address")


class MetadataSchema(BaseModel):
    """Schema for storing metadata."""
    source_system: str = Field(..., description="Source system identifier")
    source_id: str = Field(..., description="ID in the source system")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Original raw data") 