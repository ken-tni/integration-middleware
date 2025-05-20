from typing import Dict, Any, List, Optional
from datetime import datetime, date
from app.core.conversions.entity_converter import EntityConverter
from app.schemas.quotation import Quotation, QuotationItem
from app.core.exceptions import ConversionError
from app.utils.logging import get_logger
import traceback

logger = get_logger("quotation_converter")


class QuotationConverter(EntityConverter[Quotation]):
    """Converter for quotation entities between external systems and standardized schema."""
    
    def __init__(self):
        """Initialize the quotation converter with field mappings for different systems."""
        logger.info("Initializing QuotationConverter")
        self._field_mappings = {
            "erp_next": {
                # Standard to ERPNext field mapping
                "id": "name",
                "name": "name",
                "owner": "owner",
                "creation": "creation",
                "modified": "modified",
                "modified_by": "modified_by",
                "title": "title",
                "quotation_to": "quotation_to",
                "party_name": "party_name",
                "customer_name": "customer_name",
                "transaction_date": "transaction_date",
                "valid_till": "valid_till",
                "status": "status",
                "currency": "currency",
                "total": "total",
                "grand_total": "grand_total",
                "items": "items"
            },
            "cloud_erp": {
                # Standard to Cloud ERP field mapping
                "id": "quotation_id",
                "name": "quotation_number",
                "owner": "created_by",
                "creation": "created_date",
                "modified": "modified_date",
                "modified_by": "modified_by",
                "title": "title",
                "customer_name": "customer_name",
                "transaction_date": "quotation_date",
                "valid_till": "expiry_date",
                "status": "quotation_status",
                "currency": "currency_code",
                "total": "subtotal",
                "grand_total": "total_amount",
                "items": "line_items"
            }
        }
        logger.info("QuotationConverter initialized with mappings for systems: %s", list(self._field_mappings.keys()))
    
    def get_field_mapping(self, source_system: str) -> Dict[str, str]:
        """Get field mapping for a specific source system."""
        if source_system not in self._field_mappings:
            logger.warning(f"No field mapping found for source system: {source_system}")
            return {}
        return self._field_mappings[source_system]
    
    def external_to_standard(self, source_system: str, external_data: Dict[str, Any]) -> Quotation:
        """Convert from external system format to standardized schema."""
        logger.debug(f"Converting quotation from {source_system} format to standard format")
        try:
            field_mapping = self.get_field_mapping(source_system)
            if not field_mapping:
                raise ConversionError(f"No field mapping available for source system: {source_system}")
            
            # Log a sample of the external data
            logger.debug(f"External data sample: {str(external_data)[:200]}...")
            
            # Reverse the mapping for conversion from external to standard
            reverse_mapping = {v: k for k, v in field_mapping.items()}
            
            # Extract basic quotation fields
            standard_data = {
                standard_field: external_data.get(external_field)
                for external_field, standard_field in reverse_mapping.items()
                if external_field in external_data and external_field != "items"  # Handle items separately
            }
            
            # Log the standard data after mapping
            logger.debug(f"Mapped standard data: {str(standard_data)[:200]}...")
            
            # Ensure we have required fields for BaseSchema
            if "id" not in standard_data or not standard_data["id"]:
                standard_data["id"] = external_data.get("name", "")
                logger.debug(f"Added id field: {standard_data['id']}")
                
            if "created_at" not in standard_data:
                standard_data["created_at"] = self._parse_date(external_data.get("creation", datetime.now().isoformat()))
                logger.debug(f"Added created_at field: {standard_data['created_at']}")
                
            if "updated_at" not in standard_data:
                standard_data["updated_at"] = self._parse_date(external_data.get("modified", datetime.now().isoformat()))
                logger.debug(f"Added updated_at field: {standard_data['updated_at']}")
            
            # Add required fields with default values if missing
            self._add_default_values(standard_data)
            
            # Handle quotation items
            standard_data["items"] = self._convert_items(source_system, external_data)
            logger.debug(f"Converted {len(standard_data['items'])} items")
            
            # Add metadata
            standard_data["metadata"] = {
                "source_system": source_system,
                "source_id": external_data.get(field_mapping.get("id", "name"), ""),
                "raw_data": external_data
            }
            
            # Explicitly check for required fields before validation
            self._verify_required_fields(standard_data)
            
            # Log validation
            logger.debug(f"Validating standard data against Quotation schema")
            try:
                result = Quotation(**standard_data)
                logger.info(f"Successfully converted quotation from {source_system} to standard format")
                return result
            except Exception as validation_error:
                logger.error(f"Validation error: {str(validation_error)}")
                # Properly handle the validation errors from pydantic
                if hasattr(validation_error, 'errors'):
                    if callable(validation_error.errors):
                        errors = validation_error.errors()
                        for error in errors:
                            logger.error(f"Field '{error.get('loc', ['unknown'])[0]}': {error.get('msg', 'unknown error')}")
                    else:
                        for error in validation_error.errors:
                            if isinstance(error, dict):
                                logger.error(f"Field '{error.get('loc', ['unknown'])[0]}': {error.get('msg', 'unknown error')}")
                raise
            
        except Exception as e:
            logger.error(f"Error converting quotation from {source_system}: {str(e)}")
            logger.error(traceback.format_exc())
            raise ConversionError(f"Failed to convert quotation data: {str(e)}", source_system=source_system)
    
    def _add_default_values(self, standard_data: Dict[str, Any]) -> None:
        """Add default values for required fields if missing."""
        # Required fields with default values
        defaults = {
            "docstatus": 0,
            "order_type": "Sales",
            "company": "Default Company",
            "conversion_rate": 1.0,
            "selling_price_list": "Standard Selling",
            "price_list_currency": "USD",
            "plc_conversion_rate": 1.0,
            "total_qty": 0.0,
            "base_total": 0.0,
            "base_net_total": 0.0,
            "net_total": 0.0,
            "base_grand_total": 0.0,
            "quotation_to": "Customer",
            "party_name": "",
            "status": "Draft",
            "currency": "USD",
            "total": 0.0,
            "grand_total": 0.0
        }
        
        # Only add default if field is missing or None
        for field, default_value in defaults.items():
            if field not in standard_data or standard_data[field] is None:
                standard_data[field] = default_value
                logger.debug(f"Added default value for {field}: {default_value}")
        
        # Ensure required date fields
        if "transaction_date" not in standard_data or standard_data["transaction_date"] is None:
            standard_data["transaction_date"] = date.today()
            logger.debug(f"Added default transaction_date: {standard_data['transaction_date']}")
        
        # Ensure required string fields have at least an empty string
        for field in ["name", "owner", "modified_by", "customer_name"]:
            if field not in standard_data or standard_data[field] is None:
                standard_data[field] = ""
                logger.debug(f"Added default empty string for {field}")
        
        # Ensure datetime fields
        if "creation" not in standard_data or standard_data["creation"] is None:
            standard_data["creation"] = datetime.now()
            logger.debug(f"Added default creation: {standard_data['creation']}")
        
        if "modified" not in standard_data or standard_data["modified"] is None:
            standard_data["modified"] = datetime.now()
            logger.debug(f"Added default modified: {standard_data['modified']}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string into a datetime object."""
        if not date_str:
            return datetime.now()
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try with different formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                # If all formats fail, return current time
                logger.warning(f"Could not parse date string: {date_str}, using current time instead")
                return datetime.now()
            except Exception as e:
                logger.warning(f"Error parsing date: {e}, using current time instead")
                return datetime.now()
    
    def standard_to_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from standardized schema to external system format."""
        logger.debug(f"Converting quotation from standard format to {source_system} format")
        try:
            field_mapping = self.get_field_mapping(source_system)
            if not field_mapping:
                raise ConversionError(f"No field mapping available for source system: {source_system}")
            
            # Convert standard fields to external fields
            external_data = {
                external_field: standard_data.get(standard_field)
                for standard_field, external_field in field_mapping.items()
                if standard_field in standard_data and standard_field != "items"  # Handle items separately
            }
            
            # Convert items
            if "items" in standard_data and standard_data["items"]:
                external_data.update(self._format_items_for_external(source_system, standard_data))
            
            logger.info(f"Successfully converted quotation to {source_system} format")
            return external_data
            
        except Exception as e:
            logger.error(f"Error converting quotation to {source_system}: {str(e)}")
            logger.error(traceback.format_exc())
            raise ConversionError(f"Failed to convert quotation data: {str(e)}", source_system=source_system)
    
    def _convert_items(self, source_system: str, external_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert quotation items from external format to standard format."""
        items = []
        
        if source_system == "erp_next":
            raw_items = external_data.get("items", [])
            # If no items, provide a default empty item
            if not raw_items:
                logger.debug("No items found, adding a default empty item")
                return [self._create_default_item()]
                
            logger.debug(f"Converting {len(raw_items)} items from ERPNext format")
            for item in raw_items:
                items.append({
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "description": item.get("description", ""),
                    "qty": float(item.get("qty", 0)),
                    "rate": float(item.get("rate", 0)),
                    "amount": float(item.get("amount", 0)),
                    "uom": item.get("uom", "")
                })
                
        elif source_system == "cloud_erp":
            raw_items = external_data.get("line_items", [])
            # If no items, provide a default empty item
            if not raw_items:
                logger.debug("No items found, adding a default empty item")
                return [self._create_default_item()]
                
            logger.debug(f"Converting {len(raw_items)} items from Cloud ERP format")
            for item in raw_items:
                items.append({
                    "item_code": item.get("product_id", ""),
                    "item_name": item.get("product_name", ""),
                    "description": item.get("description", ""),
                    "qty": float(item.get("quantity", 0)),
                    "rate": float(item.get("unit_price", 0)),
                    "amount": float(item.get("total", 0)),
                    "uom": item.get("unit", "")
                })
                
        return items if items else [self._create_default_item()]
    
    def _create_default_item(self) -> Dict[str, Any]:
        """Create a default item when no items are found."""
        return {
            "item_code": "DEFAULT-ITEM",
            "item_name": "Default Item",
            "description": "Default item when none provided",
            "qty": 0.0,
            "rate": 0.0,
            "amount": 0.0,
            "uom": "Unit"
        }
    
    def _format_items_for_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format items from standard format to external system format."""
        result = {}
        
        if source_system == "erp_next":
            items = []
            for item in standard_data.get("items", []):
                items.append({
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "description": item.get("description", ""),
                    "qty": item.get("qty", 0),
                    "rate": item.get("rate", 0),
                    "amount": item.get("amount", 0),
                    "uom": item.get("uom", "")
                })
            result["items"] = items
            
        elif source_system == "cloud_erp":
            line_items = []
            for item in standard_data.get("items", []):
                line_items.append({
                    "product_id": item.get("item_code", ""),
                    "product_name": item.get("item_name", ""),
                    "description": item.get("description", ""),
                    "quantity": item.get("qty", 0),
                    "unit_price": item.get("rate", 0),
                    "total": item.get("amount", 0),
                    "unit": item.get("uom", "")
                })
            result["line_items"] = line_items
            
        return result
    
    def convert_filters(self, source_system: str, entity_type: str, filters: Dict[str, Any]) -> List[List[Any]]:
        """Convert standardized filters to external system format."""
        logger.debug(f"Converting filters for {entity_type} in {source_system}: {filters}")
        field_mapping = self.get_field_mapping(source_system)
        result = []
        
        # Basic field filters
        for field, value in filters.items():
            if field in field_mapping:
                external_field = field_mapping[field]
                result.append([entity_type, external_field, "=", value])
        
        # Date range filters
        if "transaction_date_from" in filters and "transaction_date" in field_mapping:
            result.append([entity_type, field_mapping["transaction_date"], ">=", filters["transaction_date_from"]])
            
        if "transaction_date_to" in filters and "transaction_date" in field_mapping:
            result.append([entity_type, field_mapping["transaction_date"], "<=", filters["transaction_date_to"]])
        
        logger.debug(f"Converted filters: {result}")        
        return result
    
    def _verify_required_fields(self, standard_data: Dict[str, Any]) -> None:
        """Verify all required fields are present with valid values before validation."""
        # List of all required fields in the Quotation schema
        required_fields = [
            "id", "name", "owner", "creation", "modified", "modified_by", "docstatus",
            "quotation_to", "party_name", "customer_name", "transaction_date", 
            "order_type", "company", "conversion_rate", "selling_price_list",
            "price_list_currency", "plc_conversion_rate", "total_qty", "base_total",
            "base_net_total", "net_total", "base_grand_total", "status", 
            "currency", "total", "grand_total", "items", "metadata"
        ]
        
        # Check each required field
        missing_fields = []
        for field in required_fields:
            if field not in standard_data or standard_data[field] is None:
                missing_fields.append(field)
                logger.warning(f"Required field '{field}' is missing or None")
                
                # Add default for missing field
                if field == "items":
                    standard_data[field] = [self._create_default_item()]
                elif field == "metadata":
                    standard_data[field] = {"source_system": "unknown", "source_id": "", "raw_data": {}}
                elif field in ["creation", "modified"]:
                    standard_data[field] = datetime.now()
                elif field == "transaction_date":
                    standard_data[field] = date.today()
                elif field in ["total", "grand_total", "total_qty", "base_total", "base_net_total", "net_total", 
                              "base_grand_total", "conversion_rate", "plc_conversion_rate"]:
                    standard_data[field] = 0.0
                elif field == "docstatus":
                    standard_data[field] = 0
                else:
                    standard_data[field] = ""
                    
                logger.info(f"Added default value for missing required field '{field}'")
        
        if missing_fields:
            logger.warning(f"Added default values for {len(missing_fields)} missing required fields: {missing_fields}") 