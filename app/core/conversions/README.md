# Centralized Conversion System

This module provides a centralized approach to data conversion between external systems and standardized schemas.

## Overview

The centralized conversion system addresses several challenges in the middleware:

1. **Consistent API Responses**: Ensures clients receive consistent data structures regardless of the backend system.
2. **Centralized Field Mapping**: All system-specific mappings are defined in one place.
3. **Easier Maintenance**: When adding new fields or systems, you only need to update the centralized converters.
4. **Better Separation of Concerns**: Adapters focus on communication with external systems, while converters handle data transformation.

## Architecture

The conversion system consists of:

- **`EntityConverter`**: Base abstract class defining the conversion interface
- **Entity-specific converters**: Specialized converters for each entity type (Customer, Product, etc.)
- **`ConverterFactory`**: Factory pattern to get the appropriate converter for each entity type

## How It Works

1. Adapters call the converter factory to get the appropriate converter
2. Converters handle the transformation between external and standard formats
3. Field mappings are centralized in each converter
4. System-specific transformations are isolated in the converters

## How to Use

### In Adapters

```python
from app.core.conversions.converter_factory import converter_factory

# Get the appropriate converter
converter = converter_factory.get_converter(entity_type)

# Convert external data to standard format
standard_data = converter.external_to_standard(source_system, external_data)

# Convert standard data to external format
external_data = converter.standard_to_external(source_system, standard_data)

# Convert filters
external_filters = converter.convert_filters(source_system, entity_type, standard_filters)
```

### Adding a New Entity Type

1. Create a schema for the entity in `app/schemas/`
2. Create a converter for the entity in `app/core/conversions/`
3. Register the converter in `ConverterFactory.__init__()`

Example:
```python
# app/core/conversions/new_entity_converter.py
from app.core.conversions.entity_converter import EntityConverter
from app.schemas.new_entity import NewEntity

class NewEntityConverter(EntityConverter[NewEntity]):
    def __init__(self):
        self.field_mappings = {
            "erp_next": {
                "id": "name",
                # Add field mappings
            },
            "cloud_erp": {
                # Add field mappings
            }
        }
    
    def external_to_standard(self, source_system, external_data):
        # Implementation
    
    def standard_to_external(self, source_system, standard_data):
        # Implementation
```

Then register in factory:
```python
# In ConverterFactory.__init__
self._converters = {
    "customer": CustomerConverter(),
    "product": ProductConverter(),
    "new_entity": NewEntityConverter(),
}
```

### Adding a New External System

1. Add the new system's field mappings to each converter:

```python
# In CustomerConverter.__init__
self.field_mappings = {
    "erp_next": { /* existing mappings */ },
    "cloud_erp": { /* existing mappings */ },
    "new_system": {
        "id": "customerID",
        "name": "customerName",
        # Add other field mappings
    }
}
```

2. If needed, add system-specific conversion logic in the converter methods:

```python
def external_to_standard(self, source_system, external_data):
    # Common code
    
    # System-specific handling
    if source_system == "new_system":
        # Handle special cases for the new system
    
    # Continue with common conversion
```

## Best Practices

1. Keep field mappings up-to-date as schemas evolve
2. Handle special cases explicitly in the converter methods
3. Use descriptive names for field mappings
4. Log important conversion steps for debugging
5. Add new mappings for each supported external system
6. Handle data type conversions explicitly
7. Implement proper error handling for conversion edge cases 