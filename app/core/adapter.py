from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generic, TypeVar, Optional

T = TypeVar('T')


class BaseAdapter(ABC, Generic[T]):
    """Base adapter interface for external systems.
    
    All adapters must implement these methods to provide a consistent
    interface regardless of the underlying system.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to the external system."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_type: str, entity_id: str) -> T:
        """Get a single entity by ID.
        
        Args:
            entity_type: The type of entity to retrieve (e.g., "customer", "product")
            entity_id: The ID of the entity in the external system
            
        Returns:
            The standardized entity object
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with the external system
        """
        pass
    
    @abstractmethod
    async def search(self, entity_type: str, filters: Dict[str, Any], 
                    page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """Search for entities with filters.
        
        Args:
            entity_type: The type of entity to search for
            filters: Dict of filter parameters
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing total count and list of entities
            
        Raises:
            AdapterError: If there's an error communicating with the external system
        """
        pass
    
    @abstractmethod
    async def create(self, entity_type: str, data: Dict[str, Any]) -> T:
        """Create a new entity in the external system.
        
        Args:
            entity_type: The type of entity to create
            data: The data for the new entity
            
        Returns:
            The created entity in standardized format
            
        Raises:
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with the external system
        """
        pass
    
    @abstractmethod
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> T:
        """Update an existing entity.
        
        Args:
            entity_type: The type of entity to update
            entity_id: The ID of the entity to update
            data: The fields to update
            
        Returns:
            The updated entity in standardized format
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with the external system
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity.
        
        Args:
            entity_type: The type of entity to delete
            entity_id: The ID of the entity to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with the external system
        """
        pass 