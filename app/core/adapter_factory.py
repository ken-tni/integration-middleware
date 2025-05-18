from typing import Dict, Type, Optional, TypeVar, Generic
from app.core.adapter import BaseAdapter
from app.adapters.erp_next.adapter import ERPNextAdapter
from app.core.exceptions import ConfigurationError
from app.utils.logging import get_logger

T = TypeVar('T')
logger = get_logger("adapter_factory")


class AdapterFactory:
    """Factory for creating and managing adapters."""
    
    def __init__(self):
        """Initialize the adapter factory."""
        self._adapters: Dict[str, Type[BaseAdapter]] = {}
        self._instances: Dict[str, BaseAdapter] = {}
        
        # Register default adapters
        self.register_adapter("erp_next", ERPNextAdapter)
    
    def register_adapter(self, name: str, adapter_class: Type[BaseAdapter]) -> None:
        """Register an adapter class.
        
        Args:
            name: The name of the adapter
            adapter_class: The adapter class
        """
        self._adapters[name] = adapter_class
        logger.debug(f"Registered adapter: {name}")
    
    async def get_adapter(self, name: str) -> BaseAdapter:
        """Get an adapter instance.
        
        Args:
            name: The name of the adapter
            
        Returns:
            An adapter instance
            
        Raises:
            ConfigurationError: If the adapter doesn't exist
        """
        # Check if adapter exists
        if name not in self._adapters:
            raise ConfigurationError(f"Adapter not found: {name}")
        
        # Create instance if it doesn't exist
        if name not in self._instances:
            adapter_class = self._adapters[name]
            self._instances[name] = adapter_class()
            await self._instances[name].connect()
            logger.info(f"Created adapter instance: {name}")
        
        return self._instances[name]
    
    async def close_all(self) -> None:
        """Close all adapter instances."""
        for name, adapter in self._instances.items():
            if hasattr(adapter, "close") and callable(getattr(adapter, "close")):
                await adapter.close()
                logger.debug(f"Closed adapter: {name}")
        
        self._instances = {}


# Create a singleton instance
adapter_factory = AdapterFactory() 