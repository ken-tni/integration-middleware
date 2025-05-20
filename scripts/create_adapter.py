#!/usr/bin/env python
import os
import sys
import argparse
import re
from datetime import datetime

# Templates for the different files to be created
ADAPTER_TEMPLATE = '''from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from app.adapters.{name}.client import {class_name}Client
from app.core.adapter import BaseAdapter
from app.core.conversions.converter_factory import converter_factory
from app.core.exceptions import EntityNotFoundError, AdapterError
from app.utils.logging import get_logger

T = TypeVar('T')
logger = get_logger("{name}_adapter")


class {class_name}Adapter(BaseAdapter[T]):
    """Adapter for {class_name} API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, client: Optional[{class_name}Client] = None):
        """Initialize the {class_name} adapter.
        
        Args:
            config: Adapter configuration dictionary
            client: Optional {class_name} client instance
        """
        self.config = config or {{}}
        self.endpoints = self.config.get("endpoints", {{}})
        self.client = client or {class_name}Client(config=self.config)
        self._entity_type_map = self.config.get("entity_map", {{}})
    
    async def connect(self) -> None:
        """Initialize connection to {class_name}."""
        # Implementation details may vary
        logger.debug("{class_name} adapter connected")
    
    async def get_by_id(self, entity_type: str, entity_id: str) -> T:
        """Get a single entity by ID from {class_name}.
        
        Args:
            entity_type: The type of entity to retrieve (e.g., "customer", "product")
            entity_id: The ID of the entity in {class_name}
            
        Returns:
            The standardized entity object
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with {class_name}
        """
        external_entity_type = self._get_external_entity_type(entity_type)
        
        try:
            # Get data from {class_name}
            path = self.endpoints["get_by_id"].format(entity_type=external_entity_type, entity_id=entity_id)
            response = await self.client.get(path)
            
            # Debug log the raw response
            logger.debug(f"Raw {{entity_type}} data from {class_name}: {{response}}")
            
            # Use centralized converter to convert to standardized format
            converter = converter_factory.get_converter(entity_type)
            return converter.external_to_standard("{name}", response.get("data", {{}}))
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting {{entity_type}} with ID {{entity_id}}: {{e}}")
            raise AdapterError(
                message=f"Failed to get {{entity_type}} with ID {{entity_id}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def search(
        self, entity_type: str, filters: Dict[str, Any], page: int = 1, page_size: int = 100
    ) -> Dict[str, Any]:
        """Search for entities in {class_name}.
        
        Args:
            entity_type: The type of entity to search for
            filters: Dict of filter parameters
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing total count and list of entities
            
        Raises:
            AdapterError: If there's an error communicating with {class_name}
        """
        external_entity_type = self._get_external_entity_type(entity_type)
        
        try:
            # Convert filters to {class_name} format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            external_filters = converter.convert_filters("{name}", entity_type, filters)
            
            # Get data from {class_name}
            path = self.endpoints["search"].format(entity_type=external_entity_type)
            params = {{
                "filters": external_filters,
                "page": page,
                "page_size": page_size,
            }}
            response = await self.client.get(path, params=params)
            
            # Convert to standardized format
            items = response.get("data", [])
            total = response.get("total", 0)
            converted_items = []
            
            for item in items:
                converted_items.append(
                    converter.external_to_standard("{name}", item)
                )
            
            # Return results in the expected format
            if entity_type == "customer":
                return {{"total": total, "customers": converted_items}}
            elif entity_type == "product":
                return {{"total": total, "products": converted_items}}
            elif entity_type == "quotation":
                return {{"total": total, "quotations": converted_items}}
            else:
                return {{"total": total, entity_type + "s": converted_items}}
        
        except Exception as e:
            logger.error(f"Error searching for {{entity_type}}: {{e}}")
            raise AdapterError(
                message=f"Failed to search for {{entity_type}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> T:
        """Create a new entity in {class_name}.
        
        Args:
            entity_type: The type of entity to create
            data: The data for the new entity
            
        Returns:
            The created entity in standardized format
            
        Raises:
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with {class_name}
        """
        external_entity_type = self._get_external_entity_type(entity_type)
        
        try:
            # Convert to {class_name} format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            external_data = converter.standard_to_external("{name}", data)
            
            # Create in {class_name}
            path = self.endpoints["create"].format(entity_type=external_entity_type)
            response = await self.client.post(path, data=external_data)
            
            # Get the created entity
            created_id = response.get("data", {{}}).get("id")
            if not created_id:
                raise AdapterError(
                    message=f"Failed to get ID of created {{entity_type}}",
                    source_system="{class_name}",
                )
            
            return await self.get_by_id(entity_type, created_id)
        
        except Exception as e:
            logger.error(f"Error creating {{entity_type}}: {{e}}")
            raise AdapterError(
                message=f"Failed to create {{entity_type}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def update(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> T:
        """Update an existing entity in {class_name}.
        
        Args:
            entity_type: The type of entity to update
            entity_id: The ID of the entity to update
            data: The fields to update
            
        Returns:
            The updated entity in standardized format
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValidationError: If the data is invalid
            AdapterError: If there's an error communicating with {class_name}
        """
        external_entity_type = self._get_external_entity_type(entity_type)
        
        try:
            # Convert to {class_name} format using centralized converter
            converter = converter_factory.get_converter(entity_type)
            external_data = converter.standard_to_external("{name}", data)
            
            # Update in {class_name}
            path = self.endpoints["update"].format(entity_type=external_entity_type, entity_id=entity_id)
            await self.client.put(path, data=external_data)
            
            # Get the updated entity
            return await self.get_by_id(entity_type, entity_id)
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating {{entity_type}} with ID {{entity_id}}: {{e}}")
            raise AdapterError(
                message=f"Failed to update {{entity_type}} with ID {{entity_id}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity in {class_name}.
        
        Args:
            entity_type: The type of entity to delete
            entity_id: The ID of the entity to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            AdapterError: If there's an error communicating with {class_name}
        """
        external_entity_type = self._get_external_entity_type(entity_type)
        
        try:
            # Delete in {class_name}
            path = self.endpoints["delete"].format(entity_type=external_entity_type, entity_id=entity_id)
            await self.client.delete(path)
            return True
        
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting {{entity_type}} with ID {{entity_id}}: {{e}}")
            raise AdapterError(
                message=f"Failed to delete {{entity_type}} with ID {{entity_id}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def close(self):
        """Close the connection to {class_name}."""
        if self.client:
            await self.client.close()
    
    def _get_external_entity_type(self, entity_type: str) -> str:
        """Get the {class_name} entity type for a standardized entity type."""
        return self._entity_type_map.get(entity_type, entity_type.capitalize())
'''

CLIENT_TEMPLATE = '''import httpx
from typing import Dict, Any, Optional
from app.core.exceptions import EntityNotFoundError, AuthenticationError, RateLimitError, AdapterError
from app.utils.logging import get_logger
from app.utils.retry import adapter_retry

logger = get_logger("{name}_client")


class {class_name}Client:
    """HTTP client for {class_name} API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the {class_name} client.
        
        Args:
            config: Configuration dictionary with API credentials
        """
        config = config or {{}}
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        
        if not self.base_url:
            raise ValueError("{class_name} base URL is required")
        
        # Remove trailing slash from base_url if present
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        
        # Initialize HTTP client with appropriate headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={{
                "Authorization": f"Bearer {{self.api_key}}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }},
            timeout=30.0,  # 30 seconds timeout
        )
        
        logger.debug(f"{class_name} client initialized with base URL: {{self.base_url}}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @adapter_retry
    async def _request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the {class_name} API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            EntityNotFoundError: If the requested entity doesn't exist
            RateLimitError: If rate limit is exceeded
            AdapterError: For other API errors
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{{path}}"
        
        url = f"{{self.base_url}}{{path}}"
        logger.debug(f"{{method}} {{url}}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            
            # Handle common HTTP errors
            if response.status_code == 401:
                raise AuthenticationError(
                    message="Authentication failed with {class_name} API",
                    source_system="{class_name}",
                )
            
            if response.status_code == 404:
                entity_type = path.strip("/").split("/")[-1]
                entity_id = params.get("id", "") if params else ""
                raise EntityNotFoundError(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    source_system="{class_name}",
                )
            
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    message="{class_name} API rate limit exceeded",
                    source_system="{class_name}",
                    retry_after=int(retry_after),
                )
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {{e}}")
            raise AdapterError(
                message=f"{class_name} API error: {{e.response.status_code}} - {{e.response.text}}",
                source_system="{class_name}",
                original_error=e,
            )
        
        except httpx.RequestError as e:
            logger.error(f"Request error: {{e}}")
            raise AdapterError(
                message=f"{class_name} API request failed: {{str(e)}}",
                source_system="{class_name}",
                original_error=e,
            )
    
    async def get(self, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a GET request to the {class_name} API."""
        return await self._request("GET", path, params=params)
    
    async def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the {class_name} API."""
        return await self._request("POST", path, json_data=data)
    
    async def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the {class_name} API."""
        return await self._request("PUT", path, json_data=data)
    
    async def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request to the {class_name} API."""
        return await self._request("DELETE", path)
'''

CONFIG_TEMPLATE = '''{{
  "adapter_name": "{name}",
  "class_path": "app.adapters.{name}.adapter.{class_name}Adapter",
  "client_class_path": "app.adapters.{name}.client.{class_name}Client",
  "base_url": "{base_url}",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "entity_map": {{
    "customer": "Customer",
    "product": "Product",
    "quotation": "Quotation"
  }},
  "endpoints": {{
    "get_by_id": "/api/v1/{{entity_type}}/{{entity_id}}",
    "search": "/api/v1/{{entity_type}}",
    "create": "/api/v1/{{entity_type}}",
    "update": "/api/v1/{{entity_type}}/{{entity_id}}",
    "delete": "/api/v1/{{entity_type}}/{{entity_id}}"
  }}
}}
'''

INIT_TEMPLATE = '''"""Adapter for {class_name} API integration."""
'''

README_TEMPLATE = '''# {class_name} Adapter

This adapter integrates with the {class_name} API to standardize data for the middleware.

## Configuration

The adapter is configured using the `config/adapters/{name}.json` file:

```json
{{
  "adapter_name": "{name}",
  "base_url": "{base_url}",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret"
}}
```

## Supported Entities

- Customers
- Products
- Quotations

## API Endpoints

- `GET /api/v1/{{entity_type}}/{{entity_id}}` - Get entity by ID
- `GET /api/v1/{{entity_type}}` - Search entities
- `POST /api/v1/{{entity_type}}` - Create entity
- `PUT /api/v1/{{entity_type}}/{{entity_id}}` - Update entity
- `DELETE /api/v1/{{entity_type}}/{{entity_id}}` - Delete entity

## Field Mappings

The field mappings between {class_name} and the standard schema are defined in:
- `app/core/conversions/customer_converter.py`
- `app/core/conversions/product_converter.py`
- `app/core/conversions/quotation_converter.py`

## Usage

```python
from app.core.adapter_factory import adapter_factory

# Get the adapter
adapter = await adapter_factory.get_adapter("{name}")

# Get a customer
customer = await adapter.get_by_id("customer", "123")

# Search for products
products = await adapter.search("product", {{"category": "Electronics"}})
```
'''

FIELD_MAPPING_TEMPLATE = '''
# Customer field mappings for {name} adapter
# Add this to app/core/conversions/customer_converter.py in __init__ method:

self.field_mappings["{name}"] = {{
    "id": "id",  # Adjust these mappings based on actual API response
    "name": "name",
    "customer_type": "type",
    "email": "email",
    "phone": "phone",
    "mobile": "mobile",
    "website": "website",
    "tax_id": "tax_id",
    "status": "status",
    "credit_limit": "credit_limit",
    "notes": "notes",
    "created_at": "created_at",
    "updated_at": "updated_at",
    # Address fields
    "address.street1": "address.line1",
    "address.street2": "address.line2",
    "address.city": "address.city",
    "address.state": "address.state",
    "address.postal_code": "address.postal_code",
    "address.country": "address.country",
}}

# Product field mappings for {name} adapter
# Add this to app/core/conversions/product_converter.py in __init__ method:

self.field_mappings["{name}"] = {{
    "id": "id",
    "name": "name",
    "sku": "sku",
    "description": "description",
    "category": "category",
    "price": "price",
    "cost": "cost",
    "tax_rate": "tax_rate",
    "stock_quantity": "stock",
    "unit_of_measure": "uom",
    "is_active": "active",
    "created_at": "created_at",
    "updated_at": "updated_at",
}}

# Note: You will also need to add similar mappings for quotations
# once the QuotationConverter is implemented
'''

def snake_to_camel(snake_str):
    """Convert snake_case to CamelCase."""
    return ''.join(x.capitalize() for x in snake_str.split('_'))

def validate_adapter_name(name):
    """Validate adapter name format."""
    if not re.match(r'^[a-z][a-z0-9_]*$', name):
        raise ValueError("Adapter name must be snake_case and start with a lowercase letter")
    return name

def create_adapter(name, base_url=None, description=None):
    """Create a new adapter with all necessary files and configuration.
    
    Args:
        name: The adapter name in snake_case
        base_url: Optional base URL for the API
        description: Optional description of the adapter
    """
    try:
        # Validate adapter name
        name = validate_adapter_name(name)
    except ValueError as e:
        print(f"Error: {e}")
        return False
    
    class_name = snake_to_camel(name)
    adapter_dir = f'app/adapters/{name}'
    
    # Set a default base URL if none provided
    if not base_url:
        base_url = f"https://api.{name}.com"
    
    # Create adapter directory
    os.makedirs(adapter_dir, exist_ok=True)
    
    # Create __init__.py
    with open(f'{adapter_dir}/__init__.py', 'w') as f:
        f.write(INIT_TEMPLATE.format(class_name=class_name))
    
    # Create adapter.py
    with open(f'{adapter_dir}/adapter.py', 'w') as f:
        f.write(ADAPTER_TEMPLATE.format(name=name, class_name=class_name))
    
    # Create client.py
    with open(f'{adapter_dir}/client.py', 'w') as f:
        f.write(CLIENT_TEMPLATE.format(name=name, class_name=class_name))
    
    # Create config directory if it doesn't exist
    os.makedirs('config/adapters', exist_ok=True)
    
    # Create config file
    with open(f'config/adapters/{name}.json', 'w') as f:
        f.write(CONFIG_TEMPLATE.format(name=name, class_name=class_name, base_url=base_url))
    
    # Create README.md for adapter
    with open(f'{adapter_dir}/README.md', 'w') as f:
        readme_content = README_TEMPLATE.format(name=name, class_name=class_name, base_url=base_url)
        if description:
            # Add description to the beginning of the README
            lines = readme_content.split('\n')
            lines.insert(2, f"\n{description}\n")
            readme_content = '\n'.join(lines)
        f.write(readme_content)
    
    # Create field mappings file
    mapping_file_path = f'{adapter_dir}/field_mappings.py'
    with open(mapping_file_path, 'w') as f:
        f.write(FIELD_MAPPING_TEMPLATE.format(name=name))
    
    # Print success message
    print(f"Adapter '{name}' created successfully!\n")
    print("--------------------------------------------------")
    print("IMPORTANT: Add field mappings to converters:")
    print("--------------------------------------------------")
    print(f"Field mapping instructions have been written to: {mapping_file_path}")
    print("Copy these mappings to the appropriate converter classes in app/core/conversions/")
    print("Then update the mappings based on the actual API response structure.\n")
    
    print(f"Adapter files created in: {adapter_dir}")
    print(f"Configuration file created in: config/adapters/{name}.json")
    print(f"README file created in: {adapter_dir}/README.md")
    
    return True

def main():
    """Parse command line arguments and create the adapter."""
    parser = argparse.ArgumentParser(
        description="Create a new adapter with all necessary files and configuration"
    )
    parser.add_argument(
        "name", 
        help="Adapter name in snake_case (e.g., cloud_erp)"
    )
    parser.add_argument(
        "--base-url", 
        help="Base URL for the API"
    )
    parser.add_argument(
        "--description", 
        help="Description of the adapter"
    )
    
    args = parser.parse_args()
    
    if create_adapter(args.name, args.base_url, args.description):
        print("\nAdapter creation completed!")

if __name__ == "__main__":
    main()