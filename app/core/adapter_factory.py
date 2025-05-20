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
                self.register_adapter(adapter_name, adapter_class, config)
                logger.info(f"Loaded adapter '{adapter_name}' from config: {config_path}")
            except Exception as e:
                print(f"Failed to load adapter from {config_path}: {e}")  # DEBUG

    def register_adapter(self, name: str, adapter_class: Type[BaseAdapter], config: Dict[str, Any]) -> None:
        self._adapters[name] = (adapter_class, config)
        logger.debug(f"Registered adapter: {name}")

    async def get_adapter(self, name: str) -> BaseAdapter:
        if name not in self._adapters:
            raise ConfigurationError(f"Adapter not found: {name}")
        if name not in self._instances:
            adapter_class, config = self._adapters[name]
            self._instances[name] = adapter_class(config=config)
            await self._instances[name].connect()
            logger.info(f"Created adapter instance: {name}")
        return self._instances[name]

    async def close_all(self) -> None:
        for name, adapter in self._instances.items():
            if hasattr(adapter, "close") and callable(getattr(adapter, "close")):
                await adapter.close()
                logger.debug(f"Closed adapter: {name}")
        self._instances = {}


adapter_factory = AdapterFactory() 