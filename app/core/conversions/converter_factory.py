from typing import Dict, Any, Type, TypeVar, Generic
from app.core.conversions.entity_converter import EntityConverter
from app.core.conversions.customer_converter import CustomerConverter
from app.core.conversions.product_converter import ProductConverter
from app.core.conversions.invoice_converter import InvoiceConverter
from app.core.conversions.quotation_converter import QuotationConverter
from app.core.exceptions import ConfigurationError
from app.utils.logging import get_logger

logger = get_logger("converter_factory")

T = TypeVar('T')


class ConverterFactory:
    """Factory for creating and managing entity converters."""
    
    def __init__(self):
        """Initialize the converter factory with all available converters."""
        self._converters = {
            "customer": CustomerConverter(),
            "product": ProductConverter(),
            "invoice": InvoiceConverter(),
            "quotation": QuotationConverter(),
            # Add other converters here as they are implemented
        }
        logger.info(f"Initialized converter factory with converters: {list(self._converters.keys())}")
    
    def get_converter(self, entity_type: str) -> EntityConverter:
        """Get converter for a specific entity type.
        
        Args:
            entity_type: The type of entity to get a converter for (e.g., "customer", "product")
            
        Returns:
            The appropriate entity converter
            
        Raises:
            ConfigurationError: If no converter is found for the entity type
        """
        if entity_type not in self._converters:
            logger.error(f"No converter found for entity type: {entity_type}")
            raise ConfigurationError(f"No converter found for entity type: {entity_type}")
        
        logger.debug(f"Retrieved converter for entity type: {entity_type}")
        return self._converters[entity_type]
    
    def register_converter(self, entity_type: str, converter: EntityConverter) -> None:
        """Register a new converter.
        
        Args:
            entity_type: The type of entity this converter handles
            converter: The converter instance
        """
        self._converters[entity_type] = converter
        logger.info(f"Registered converter for entity type: {entity_type}")


# Create a singleton instance
converter_factory = ConverterFactory() 