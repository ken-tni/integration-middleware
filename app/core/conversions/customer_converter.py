from typing import Dict, Any, Optional, List
from app.core.conversions.entity_converter import EntityConverter
from app.schemas.customer import Customer
from app.schemas.base import Address, ContactInfo, MetadataSchema
from app.utils.logging import get_logger

logger = get_logger("customer_converter")


class CustomerConverter(EntityConverter[Customer]):
    """Converter for Customer entities."""
    
    def __init__(self):
        """Initialize the customer converter with field mappings for different systems."""
        # Define field mappings for different source systems (standard_field: external_field)
        self.field_mappings = {
            "erp_next": {
                "id": "name",
                "name": "customer_name",
                "customer_type": "customer_type",
                "email": "email_id",
                "phone": "phone",
                "mobile": "mobile_no",
                "website": "website",
                "tax_id": "tax_id",
                "status": "status",
                "credit_limit": "credit_limit",
                "notes": "notes",
                "created_at": "creation",
                "updated_at": "modified",
                "owner": "owner",
                "modified_by": "modified_by",
                "docstatus": "docstatus",
                "naming_series": "naming_series",
                "salutation": "salutation",
                "customer_group": "customer_group",
                "territory": "territory",
                "gender": "gender",
                "lead_name": "lead_name",
                "opportunity_name": "opportunity_name",
                "prospect_name": "prospect_name",
                "account_manager": "account_manager",
                "image": "image",
                "language": "language",
                "market_segment": "market_segment",
                "default_currency": "default_currency",
                # Address fields
                "address.street1": "address_line1",
                "address.street2": "address_line2",
                "address.city": "city",
                "address.state": "state",
                "address.postal_code": "pincode",
                "address.country": "country",
            },
            "cloud_erp": {
                "id": "customer_id",
                "name": "name",
                "customer_type": "type",
                "email": "email_address",
                "phone": "phone_number",
                "mobile": "mobile_number",
                "website": "web_site",
                "tax_id": "tax_identifier",
                "status": "status",
                "credit_limit": "credit_limit_amount",
                "notes": "customer_notes",
                "created_at": "created_date",
                "updated_at": "last_modified_date",
                # Address fields
                "address.street1": "street",
                "address.street2": "street2",
                "address.city": "city",
                "address.state": "state",
                "address.postal_code": "zip",
                "address.country": "country",
            },
            # Add mappings for other systems as needed
        }
    
    def get_field_mapping(self, source_system: str) -> Dict[str, str]:
        """Get field mapping for a specific source system."""
        return self.field_mappings.get(source_system, {})
    
    def external_to_standard(self, source_system: str, external_data: Dict[str, Any]) -> Customer:
        """Convert from external system format to standardized customer schema."""
        mapping = self.get_field_mapping(source_system)
        
        # Log available fields for debugging
        logger.debug(f"Available fields in {source_system} customer: {list(external_data.keys())}")
        
        # Extract address if available
        address = self._extract_address(source_system, external_data)
        
        # Create standardized customer
        return Customer(
            id=external_data.get(mapping.get("id", "id"), ""),
            name=external_data.get(mapping.get("name", "name"), ""),
            customer_type=external_data.get(mapping.get("customer_type", "customer_type"), "Company"),
            contact_info=ContactInfo(
                email=external_data.get(mapping.get("email", "email")),
                phone=external_data.get(mapping.get("phone", "phone")),
                mobile=external_data.get(mapping.get("mobile", "mobile")),
                website=external_data.get(mapping.get("website", "website")),
                address=address,
            ),
            tax_id=external_data.get(mapping.get("tax_id", "tax_id")),
            status=external_data.get(mapping.get("status", "status"), "Active"),
            credit_limit=float(external_data.get(mapping.get("credit_limit", "credit_limit"), 0)) 
                if external_data.get(mapping.get("credit_limit", "credit_limit")) 
                else None,
            notes=external_data.get(mapping.get("notes", "notes")),
            created_at=self._parse_date(external_data.get(mapping.get("created_at", "created_at"))),
            updated_at=self._parse_date(external_data.get(mapping.get("updated_at", "updated_at"))),
            # Additional ERPNext fields
            owner=external_data.get(mapping.get("owner", "owner")),
            modified_by=external_data.get(mapping.get("modified_by", "modified_by")),
            docstatus=external_data.get(mapping.get("docstatus", "docstatus")),
            naming_series=external_data.get(mapping.get("naming_series", "naming_series")),
            salutation=external_data.get(mapping.get("salutation", "salutation")),
            customer_group=external_data.get(mapping.get("customer_group", "customer_group")),
            territory=external_data.get(mapping.get("territory", "territory")),
            gender=external_data.get(mapping.get("gender", "gender")),
            lead_name=external_data.get(mapping.get("lead_name", "lead_name")),
            opportunity_name=external_data.get(mapping.get("opportunity_name", "opportunity_name")),
            prospect_name=external_data.get(mapping.get("prospect_name", "prospect_name")),
            account_manager=external_data.get(mapping.get("account_manager", "account_manager")),
            image=external_data.get(mapping.get("image", "image")),
            language=external_data.get(mapping.get("language", "language")),
            market_segment=external_data.get(mapping.get("market_segment", "market_segment")),
            default_currency=external_data.get(mapping.get("default_currency", "default_currency")),
            metadata=MetadataSchema(
                source_system=source_system,
                source_id=external_data.get(mapping.get("id", "id"), ""),
                raw_data=external_data,
            ),
        )
    
    def standard_to_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from standardized schema to external system format."""
        mapping = self.get_field_mapping(source_system)
        
        # Create initial result dict
        result = {}
        
        # System-specific transformations
        if source_system == "erp_next":
            result["doctype"] = "Customer"
        
        # Map standard fields to external fields
        for std_field, value in standard_data.items():
            if std_field == "contact_info":
                # Handle contact info separately
                contact_info = value if isinstance(value, dict) else value.dict() if hasattr(value, "dict") else {}
                
                # Add direct contact fields
                for contact_field in ["email", "phone", "mobile", "website"]:
                    if contact_info.get(contact_field):
                        ext_field = mapping.get(contact_field, contact_field)
                        result[ext_field] = contact_info.get(contact_field)
                
                # Add address fields
                address = contact_info.get("address")
                if address:
                    address_dict = address if isinstance(address, dict) else address.dict() if hasattr(address, "dict") else {}
                    for addr_field, addr_value in address_dict.items():
                        addr_mapping_key = f"address.{addr_field}"
                        if addr_mapping_key in mapping:
                            result[mapping[addr_mapping_key]] = addr_value
            elif std_field == "metadata":
                # Skip metadata field
                continue
            else:
                # Map regular fields
                ext_field = mapping.get(std_field, std_field)
                result[ext_field] = value
        
        # Remove None values to avoid overwrites
        return {k: v for k, v in result.items() if v is not None}
    
    def convert_filters(self, source_system: str, entity_type: str, 
                       filters: Dict[str, Any]) -> List[List[Any]]:
        """Convert standardized filters to external system format."""
        mapping = self.get_field_mapping(source_system)
        result = []
        
        for field, value in filters.items():
            # Map the field name if needed
            ext_field = mapping.get(field, field)
            
            # Handle special cases based on system
            if source_system == "erp_next":
                # Standard case for ERPNext
                result.append([ext_field, "=", value])
            elif source_system == "cloud_erp":
                # CloudERP may have different filter format
                result.append({"field": ext_field, "operator": "eq", "value": value})
        
        return result
    
    def _extract_address(self, source_system: str, external_data: Dict[str, Any]) -> Optional[Address]:
        """Extract address from external data based on source system."""
        mapping = self.get_field_mapping(source_system)
        
        # Get mapped field names for address components
        street1_field = mapping.get("address.street1", "address_line1")
        street2_field = mapping.get("address.street2", "address_line2")
        city_field = mapping.get("address.city", "city")
        state_field = mapping.get("address.state", "state")
        postal_code_field = mapping.get("address.postal_code", "postal_code")
        country_field = mapping.get("address.country", "country")
        
        # Check if primary address field exists
        if external_data.get(street1_field):
            return Address(
                street1=external_data.get(street1_field, ""),
                street2=external_data.get(street2_field, ""),
                city=external_data.get(city_field, ""),
                state=external_data.get(state_field, ""),
                postal_code=external_data.get(postal_code_field, ""),
                country=external_data.get(country_field, ""),
            )
        return None 