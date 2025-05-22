from typing import Dict, Any, Callable, List
import importlib
import inspect
from app.utils.logging import get_logger
from app.utils.json_utils import deep_serialize

logger = get_logger("core.websocket_service")

class WebSocketService:
    """
    Service to handle WebSocket requests and route them to appropriate endpoints
    """
    def __init__(self):
        self._endpoint_handlers = {}
        
    def register_handler(self, endpoint: str, handler: Callable):
        """Register a handler function for an endpoint"""
        self._endpoint_handlers[endpoint] = handler
        
    async def handle_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request for a specific endpoint"""
        if endpoint not in self._endpoint_handlers:
            return {
                "status": "error",
                "message": f"Unknown endpoint: {endpoint}"
            }
        
        try:
            handler = self._endpoint_handlers[endpoint]
            result = await handler(params) if inspect.iscoroutinefunction(handler) else handler(params)
            
            # Serialize the result to ensure it's JSON serializable
            serialized_result = deep_serialize(result)
            
            return {
                "status": "success",
                "data": serialized_result
            }
        except Exception as e:
            logger.error(f"Error handling WebSocket request to '{endpoint}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }
    
    def auto_register_endpoint_modules(self, modules_list: List[str]):
        """
        Automatically register endpoint handlers from specified modules
        
        Args:
            modules_list: List of module paths to import and register handlers from
        """
        for module_path in modules_list:
            try:
                module = importlib.import_module(module_path)
                
                # Look for exposed endpoints in the module
                for name, obj in inspect.getmembers(module):
                    if hasattr(obj, "_ws_endpoint") and obj._ws_endpoint:
                        endpoint_name = getattr(obj, "_ws_endpoint_name", name)
                        self.register_handler(endpoint_name, obj)
                        logger.info(f"Registered WebSocket handler for endpoint: {endpoint_name}")
                        
            except ImportError as e:
                logger.error(f"Failed to import module {module_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error registering endpoints from {module_path}: {str(e)}")

# Create decorator for marking WebSocket endpoint handlers
def ws_endpoint(name=None):
    """Decorator to mark a function as a WebSocket endpoint handler"""
    def decorator(func):
        func._ws_endpoint = True
        if name:
            func._ws_endpoint_name = name
        return func
    return decorator

# Singleton instance
websocket_service = WebSocketService() 