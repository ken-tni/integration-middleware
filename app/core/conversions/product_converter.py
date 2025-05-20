from typing import Dict, Any, Optional, List
from app.core.conversions.entity_converter import EntityConverter
from app.schemas.product import Product, ProductAttribute
from app.schemas.base import MetadataSchema
from app.utils.logging import get_logger

logger = get_logger("product_converter")


class ProductConverter(EntityConverter[Product]):
    """Converter for Product entities."""
    
    def __init__(self):
        """Initialize the product converter with field mappings for different systems."""
        # Define field mappings for different source systems (standard_field: external_field)
        self.field_mappings = {
            "erp_next": {
                "id": "name",
                "name": "item_name",
                "sku": "item_code",
                "description": "description",
                "category": "item_group",
                "price": "standard_rate",
                "cost": "valuation_rate",
                "tax_rate": "tax_rate",
                "stock_quantity": "actual_qty",
                "unit_of_measure": "stock_uom",
                "is_active": "disabled",  # Note: this is inverted in ERPNext
                "created_at": "creation",
                "updated_at": "modified",
            },
            "cloud_erp": {
                "id": "product_id",
                "name": "product_name",
                "sku": "sku",
                "description": "description",
                "category": "category",
                "price": "price",
                "cost": "cost",
                "tax_rate": "tax_percentage",
                "stock_quantity": "quantity_in_stock",
                "unit_of_measure": "uom",
                "is_active": "active",
                "created_at": "created_date",
                "updated_at": "last_modified_date",
            },
            # Add mappings for other systems as needed
        }
    
    def get_field_mapping(self, source_system: str) -> Dict[str, str]:
        """Get field mapping for a specific source system."""
        return self.field_mappings.get(source_system, {})
    
    def external_to_standard(self, source_system: str, external_data: Dict[str, Any]) -> Product:
        """Convert from external system format to standardized product schema."""
        mapping = self.get_field_mapping(source_system)
        
        # Log available fields for debugging
        logger.debug(f"Available fields in {source_system} product: {list(external_data.keys())}")
        
        # Extract attributes based on source system
        attributes = self._extract_attributes(source_system, external_data)
        
        # Handle special cases based on source system
        is_active = True
        if source_system == "erp_next":
            # ERPNext uses "disabled" which is the inverse of "is_active"
            is_active = not external_data.get(mapping.get("is_active", "disabled"), False)
        else:
            is_active = external_data.get(mapping.get("is_active", "is_active"), True)
        
        # Create standardized product
        return Product(
            id=external_data.get(mapping.get("id", "id"), ""),
            name=external_data.get(mapping.get("name", "name"), ""),
            sku=external_data.get(mapping.get("sku", "sku"), ""),
            description=external_data.get(mapping.get("description", "description"), ""),
            category=external_data.get(mapping.get("category", "category"), ""),
            price=float(external_data.get(mapping.get("price", "price"), 0)),
            cost=float(external_data.get(mapping.get("cost", "cost"), 0)) 
                if external_data.get(mapping.get("cost", "cost")) is not None 
                else None,
            tax_rate=float(external_data.get(mapping.get("tax_rate", "tax_rate"), 0)) 
                if external_data.get(mapping.get("tax_rate", "tax_rate")) is not None 
                else None,
            stock_quantity=int(external_data.get(mapping.get("stock_quantity", "stock_quantity"), 0)),
            unit_of_measure=external_data.get(mapping.get("unit_of_measure", "unit_of_measure"), ""),
            attributes=attributes,
            is_active=is_active,
            created_at=self._parse_date(external_data.get(mapping.get("created_at", "created_at"))),
            updated_at=self._parse_date(external_data.get(mapping.get("updated_at", "updated_at"))),
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
            result["doctype"] = "Item"
            # Handle is_active as disabled (inverted)
            if "is_active" in standard_data:
                result["disabled"] = not standard_data["is_active"]
        
        # Map standard fields to external fields
        for std_field, value in standard_data.items():
            # Skip already handled fields
            if std_field == "is_active" and source_system == "erp_next":
                continue
            elif std_field == "metadata":
                continue
            elif std_field == "attributes":
                # Handle attributes based on source system
                self._convert_attributes(source_system, value, result)
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
            
            # Handle special cases
            if field == "is_active" and source_system == "erp_next":
                # ERPNext uses "disabled" which is the inverse of "is_active"
                result.append([ext_field, "=", not value])
            else:
                # Standard case
                if source_system == "erp_next":
                    result.append([ext_field, "=", value])
                elif source_system == "cloud_erp":
                    result.append({"field": ext_field, "operator": "eq", "value": value})
        
        return result
    
    def _extract_attributes(self, source_system: str, external_data: Dict[str, Any]) -> List[ProductAttribute]:
        """Extract product attributes from external data based on source system."""
        attributes = []
        
        if source_system == "erp_next":
            # ERPNext stores attributes in a list of dicts
            for attr in external_data.get("attributes", []):
                attributes.append(ProductAttribute(
                    name=attr.get("attribute", ""),
                    value=attr.get("attribute_value", ""),
                ))
        elif source_system == "cloud_erp":
            # CloudERP might store attributes differently
            attrs_data = external_data.get("attributes", {})
            if isinstance(attrs_data, dict):
                # If attributes are stored as a dict of name/value pairs
                for name, value in attrs_data.items():
                    attributes.append(ProductAttribute(name=name, value=value))
        
        return attributes
    
    def _convert_attributes(self, source_system: str, attributes: List[Dict[str, Any]], result: Dict[str, Any]) -> None:
        """Convert attributes to external system format and add to result dict."""
        if not attributes:
            return
        
        if source_system == "erp_next":
            # Convert to ERPNext attribute format
            erp_attributes = []
            for attr in attributes:
                attr_dict = attr if isinstance(attr, dict) else attr.dict() if hasattr(attr, "dict") else {}
                erp_attributes.append({
                    "attribute": attr_dict.get("name", ""),
                    "attribute_value": attr_dict.get("value", ""),
                })
            result["attributes"] = erp_attributes
        elif source_system == "cloud_erp":
            # Convert to CloudERP attribute format (example)
            cloud_attributes = {}
            for attr in attributes:
                attr_dict = attr if isinstance(attr, dict) else attr.dict() if hasattr(attr, "dict") else {}
                cloud_attributes[attr_dict.get("name", "")] = attr_dict.get("value", "")
            result["attributes"] = cloud_attributes 