import os
import glob
import importlib
import json
from typing import Dict, Type, Optional, TypeVar, Generic, Any
from app.core.adapter import BaseAdapter
from app.core.exceptions import ConfigurationError
from app.utils.logging import get_logger

T = TypeVar('T')
logger = get_logger("adapter_factory")

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/adapters'))

class AdapterFactory:
    """Factory for creating and managing adapters."""
    
    def __init__(self):
        print("AdapterFactory __init__ running")
        self._adapters: Dict[str, Type[BaseAdapter]] = {}
        self._instances: Dict[str, BaseAdapter] = {}
        self._session_instances: Dict[str, Dict[str, BaseAdapter]] = {}  # user_id -> {adapter_name -> instance}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_adapters_from_config()

    def _load_adapters_from_config(self):
        print("AdapterFactory _load_adapters_from_config running")
        print(f"CONFIG_DIR: {CONFIG_DIR}")
        pattern = os.path.join(CONFIG_DIR, "*.json")
        config_files = glob.glob(pattern)
        print(f"Config files found: {config_files}")
        for config_path in config_files:
            print(f"Loading adapter config: {config_path}")  # DEBUG
            with open(config_path, "r") as f:
                config = json.load(f)
            try:
                adapter_name = config["adapter_name"]
                class_path = config["class_path"]
                module_name, class_name = class_path.rsplit(".", 1)
                print(f"Importing {module_name}.{class_name}")  # DEBUG
                module = importlib.import_module(module_name)
                adapter_class = getattr(module, class_name)
                
                # Set default auth_method if not specified
                if "auth_method" not in config:
                    # If auth_endpoint exists, default to password auth
                    if "auth_endpoint" in config:
                        config["auth_method"] = "password"
                    else:
                        config["auth_method"] = "token"
                        
                self.register_adapter(adapter_name, adapter_class, config)
                logger.info(f"Loaded adapter '{adapter_name}' from config: {config_path}")
            except Exception as e:
                print(f"Failed to load adapter from {config_path}: {e}")  # DEBUG

    def register_adapter(self, name: str, adapter_class: Type[BaseAdapter], config: Dict[str, Any]) -> None:
        """Register an adapter class and its configuration."""
        self._adapters[name] = (adapter_class, config)
        self._configs[name] = config
        logger.debug(f"Registered adapter: {name} (auth method: {config.get('auth_method', 'token')})")

    async def get_adapter(self, name: str, session_id: Optional[str] = None,
                         auth_headers: Optional[Dict[str, str]] = None,
                         auth_cookies: Optional[Dict[str, str]] = None) -> BaseAdapter:
        """Get an adapter instance.
        
        For token-based authentication, the adapter client will handle authentication internally
        by using the API key and secret from the configuration.
        
        For session-based authentication, session credentials can be provided.
        """
        if name not in self._adapters:
            raise ConfigurationError(f"Adapter not found: {name}")
        
        adapter_class, config = self._adapters[name]
        auth_method = config.get("auth_method", "token")
        
        # For session-based authentication with credentials, create a new instance
        if auth_method == "password" and (session_id or auth_headers or auth_cookies):
            # Create an instance with session authentication
            adapter = adapter_class(
                config=config,
                session_id=session_id,
                auth_headers=auth_headers,
                auth_cookies=auth_cookies
            )
            await adapter.connect()
            return adapter
        
        # Use existing instance if available for token-based auth or when no session provided
        if name not in self._instances:
            self._instances[name] = adapter_class(config=config)
            await self._instances[name].connect()
            logger.info(f"Created adapter instance: {name}")
            
        return self._instances[name]
    
    def get_adapter_config(self, name: str) -> Dict[str, Any]:
        """Get the configuration for an adapter."""
        if name not in self._configs:
            raise ConfigurationError(f"Adapter configuration not found: {name}")
        return self._configs[name]
    
    def get_auth_method(self, name: str) -> str:
        """Get the authentication method for an adapter."""
        config = self.get_adapter_config(name)
        return config.get("auth_method", "token")

    async def close_all(self) -> None:
        """Close all adapter instances."""
        # Close standard instances
        for name, adapter in self._instances.items():
            if hasattr(adapter, "close") and callable(getattr(adapter, "close")):
                await adapter.close()
                logger.debug(f"Closed adapter: {name}")
        
        # Close session instances
        for user_id, adapters in self._session_instances.items():
            for name, adapter in adapters.items():
                if hasattr(adapter, "close") and callable(getattr(adapter, "close")):
                    await adapter.close()
                    logger.debug(f"Closed session adapter for user {user_id}, adapter {name}")
        
        self._instances = {}
        self._session_instances = {}


adapter_factory = AdapterFactory() 