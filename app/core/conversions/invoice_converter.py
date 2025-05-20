from typing import Dict, Any, List, cast
from app.core.conversions.entity_converter import EntityConverter
from app.schemas.invoice import Invoice
from app.core.exceptions import ConversionError
from app.utils.logging import get_logger

logger = get_logger("invoice_converter")


class InvoiceConverter(EntityConverter[Invoice]):
    """Converter for invoice entities between external systems and standardized schema."""
    
    def __init__(self):
        """Initialize the invoice converter with field mappings for different systems."""
        self._field_mappings = {
            "erp_next": {
                # Standard to ERPNext field mapping
                "id": "name",
                "number": "name",
                "customer_id": "customer",
                "invoice_date": "posting_date",
                "due_date": "due_date",
                "status": "status",
                "currency": "currency",
                "subtotal": "net_total",
                "tax_total": "total_taxes_and_charges",
                "discount_total": "discount_amount",
                "grand_total": "grand_total",
                "notes": "remarks",
                "payment_terms": "payment_terms_template"
            },
            "cloud_erp": {
                # Standard to Cloud ERP field mapping
                "id": "invoice_id",
                "number": "invoice_number",
                "customer_id": "customer_id",
                "invoice_date": "issue_date",
                "due_date": "due_date",
                "status": "invoice_status",
                "currency": "currency_code",
                "subtotal": "subtotal",
                "tax_total": "tax_amount", 
                "discount_total": "discount_amount",
                "grand_total": "total_amount",
                "notes": "notes",
                "payment_terms": "payment_terms"
            }
        }
    
    def get_field_mapping(self, source_system: str) -> Dict[str, str]:
        """Get field mapping for a specific source system."""
        if source_system not in self._field_mappings:
            logger.warning(f"No field mapping found for source system: {source_system}")
            return {}
        return self._field_mappings[source_system]
    
    def external_to_standard(self, source_system: str, external_data: Dict[str, Any]) -> Invoice:
        """Convert from external system format to standardized schema."""
        try:
            field_mapping = self.get_field_mapping(source_system)
            if not field_mapping:
                raise ConversionError(f"No field mapping available for source system: {source_system}")
            
            # Reverse the mapping for conversion from external to standard
            reverse_mapping = {v: k for k, v in field_mapping.items()}
            
            # Extract basic invoice fields
            standard_data = {
                standard_field: external_data.get(external_field)
                for external_field, standard_field in reverse_mapping.items()
                if external_field in external_data
            }
            
            # Build metadata
            standard_data["metadata"] = {
                "source_system": source_system,
                "source_id": external_data.get(field_mapping.get("id", "name"), "unknown"),
                "raw_data": external_data
            }
            
            # Process items based on the source system
            standard_data["items"] = self._process_items(source_system, external_data)
            
            # Process addresses based on the source system
            self._process_addresses(source_system, external_data, standard_data)
            
            # Ensure required datetime fields
            standard_data["created_at"] = self._parse_date(external_data.get("creation", external_data.get("created_at")))
            standard_data["updated_at"] = self._parse_date(external_data.get("modified", external_data.get("updated_at")))
            
            return Invoice(**standard_data)
        
        except Exception as e:
            logger.error(f"Error converting invoice from {source_system}: {str(e)}")
            raise ConversionError(f"Failed to convert invoice data: {str(e)}")
    
    def standard_to_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from standardized schema to external system format."""
        try:
            field_mapping = self.get_field_mapping(source_system)
            if not field_mapping:
                raise ConversionError(f"No field mapping available for source system: {source_system}")
            
            # Convert standard fields to external fields
            external_data = {
                external_field: standard_data.get(standard_field)
                for standard_field, external_field in field_mapping.items()
                if standard_field in standard_data
            }
            
            # Process items for the specific external system
            if "items" in standard_data:
                external_data.update(self._format_items_for_external(source_system, standard_data))
            
            # Process addresses for the specific external system
            self._format_addresses_for_external(source_system, standard_data, external_data)
            
            return external_data
        
        except Exception as e:
            logger.error(f"Error converting invoice to {source_system}: {str(e)}")
            raise ConversionError(f"Failed to convert invoice data: {str(e)}")
    
    def _process_items(self, source_system: str, external_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process invoice items based on the source system structure."""
        items = []
        
        if source_system == "erp_next":
            # ERPNext stores items in a "items" array
            for item in external_data.get("items", []):
                items.append({
                    "product_id": item.get("item_code", ""),
                    "description": item.get("description", ""),
                    "quantity": float(item.get("qty", 0)),
                    "unit_price": float(item.get("rate", 0)),
                    "discount_percentage": float(item.get("discount_percentage", 0)),
                    "tax_percentage": self._calculate_tax_percentage(item),
                    "total_amount": float(item.get("amount", 0))
                })
                
        elif source_system == "cloud_erp":
            # Cloud ERP might have a different structure
            for item in external_data.get("line_items", []):
                items.append({
                    "product_id": item.get("product_id", ""),
                    "description": item.get("description", ""),
                    "quantity": float(item.get("quantity", 0)),
                    "unit_price": float(item.get("unit_price", 0)),
                    "discount_percentage": float(item.get("discount_percent", 0)),
                    "tax_percentage": float(item.get("tax_percent", 0)),
                    "total_amount": float(item.get("total", 0))
                })
                
        return items
    
    def _format_items_for_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format items from standard format to external system format."""
        result = {}
        
        if source_system == "erp_next":
            items = []
            for item in standard_data.get("items", []):
                items.append({
                    "item_code": item.get("product_id", ""),
                    "description": item.get("description", ""),
                    "qty": item.get("quantity", 0),
                    "rate": item.get("unit_price", 0),
                    "discount_percentage": item.get("discount_percentage", 0),
                    "amount": item.get("total_amount", 0)
                })
            result["items"] = items
            
        elif source_system == "cloud_erp":
            line_items = []
            for item in standard_data.get("items", []):
                line_items.append({
                    "product_id": item.get("product_id", ""),
                    "description": item.get("description", ""),
                    "quantity": item.get("quantity", 0),
                    "unit_price": item.get("unit_price", 0),
                    "discount_percent": item.get("discount_percentage", 0),
                    "tax_percent": item.get("tax_percentage", 0),
                    "total": item.get("total_amount", 0)
                })
            result["line_items"] = line_items
            
        return result
    
    def _process_addresses(self, source_system: str, external_data: Dict[str, Any], standard_data: Dict[str, Any]) -> None:
        """Process addresses from external data to standard format."""
        # Implementation will depend on how addresses are structured in each system
        pass
    
    def _format_addresses_for_external(self, source_system: str, standard_data: Dict[str, Any], external_data: Dict[str, Any]) -> None:
        """Format addresses from standard format to external system format."""
        # Implementation will depend on how addresses are structured in each system
        pass
    
    def _calculate_tax_percentage(self, item: Dict[str, Any]) -> float:
        """Calculate the tax percentage from an ERPNext item."""
        # This will depend on how taxes are structured in the external system
        return 0.0
    
    def convert_filters(self, source_system: str, entity_type: str, filters: Dict[str, Any]) -> List[List[Any]]:
        """Convert standardized filters to external system format."""
        field_mapping = self.get_field_mapping(source_system)
        result = []
        
        for field, value in filters.items():
            if field in field_mapping:
                external_field = field_mapping[field]
                result.append([entity_type, external_field, "=", value])
                
        return result 