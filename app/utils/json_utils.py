from typing import Any, Dict, List
import json
from datetime import date, datetime
import decimal
import uuid

def to_serializable(obj: Any) -> Any:
    """
    Convert a Python object to a JSON serializable type.
    
    Handles:
    - Pydantic models via their dict() or model_dump() methods
    - datetime objects
    - date objects
    - Decimal objects
    - UUID objects
    - Objects with a to_dict() method
    - Objects with a __dict__ attribute
    
    Args:
        obj: The object to convert
        
    Returns:
        A JSON serializable representation of the object
    """
    # Handle None
    if obj is None:
        return None
        
    # Handle Pydantic v1 models
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()
        
    # Handle Pydantic v2 models
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return obj.model_dump()
        
    # Handle datetime objects
    if isinstance(obj, datetime):
        return obj.isoformat()
        
    # Handle date objects
    if isinstance(obj, date):
        return obj.isoformat()
        
    # Handle Decimal objects
    if isinstance(obj, decimal.Decimal):
        return float(obj)
        
    # Handle UUID objects
    if isinstance(obj, uuid.UUID):
        return str(obj)
        
    # Handle objects with to_dict method
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
        
    # Handle objects with __dict__ attribute (generic objects)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
        
    # Handle lists
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
        
    # Handle dictionaries
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
        
    # For any other type, try to convert to string or let default JSON encoder handle it
    try:
        return str(obj)
    except:
        return obj

def deep_serialize(data: Any) -> Any:
    """
    Recursively convert an object and all its nested properties to JSON serializable types.
    
    Args:
        data: The data to serialize (can be a dict, list, or any object)
        
    Returns:
        JSON serializable data structure
    """
    if isinstance(data, dict):
        return {key: deep_serialize(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [deep_serialize(item) for item in data]
    else:
        return to_serializable(data)

class EnhancedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles common types not natively supported by JSON."""
    
    def default(self, obj):
        serialized = to_serializable(obj)
        if serialized is obj:  # If no conversion was made
            return super().default(obj)
        return serialized

def dumps(obj: Any, **kwargs) -> str:
    """
    Serialize object to a JSON formatted string with enhanced type support.
    
    Args:
        obj: The Python object to serialize
        **kwargs: Additional arguments to pass to json.dumps
        
    Returns:
        JSON string representation
    """
    return json.dumps(deep_serialize(obj), **kwargs) 