from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, List, Optional

T = TypeVar('T')


class EntityConverter(ABC, Generic[T]):
    """Base interface for entity converters.
    
    All entity converters must implement these methods to provide a consistent
    interface for converting between external system formats and standardized schemas.
    """
    
    @abstractmethod
    def external_to_standard(self, source_system: str, external_data: Dict[str, Any]) -> T:
        """Convert from external system format to standardized schema.
        
        Args:
            source_system: The source system identifier (e.g., "erp_next", "cloud_erp")
            external_data: Data from the external system
            
        Returns:
            Standardized entity object
        """
        pass
    
    @abstractmethod
    def standard_to_external(self, source_system: str, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from standardized schema to external system format.
        
        Args:
            source_system: The target system identifier (e.g., "erp_next", "cloud_erp")
            standard_data: Data in the standardized format
            
        Returns:
            Data formatted for the external system
        """
        pass
    
    def get_field_mapping(self, source_system: str) -> Dict[str, str]:
        """Get field mapping for a specific source system.
        
        Args:
            source_system: The source system identifier
            
        Returns:
            Dictionary mapping standard field names to external system field names
        """
        pass
    
    def convert_filters(self, source_system: str, entity_type: str, 
                       filters: Dict[str, Any]) -> List[List[Any]]:
        """Convert standardized filters to external system format.
        
        Args:
            source_system: The source system identifier
            entity_type: The type of entity being filtered
            filters: Dictionary of filter parameters in standardized format
            
        Returns:
            Filters formatted for the external system
        """
        pass
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[Any]:
        """Parse date string from external system.
        
        Args:
            date_str: Date string from external system
            
        Returns:
            Parsed datetime object or None
        """
        if not date_str:
            return None
        try:
            from datetime import datetime
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None 