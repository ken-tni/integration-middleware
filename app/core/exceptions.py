class MiddlewareError(Exception):
    """Base exception for all middleware errors."""
    def __init__(self, message: str = "An error occurred in the middleware"):
        self.message = message
        super().__init__(self.message)


class AdapterError(MiddlewareError):
    """Exception raised when there's an error in an adapter."""
    def __init__(self, message: str = "Error communicating with external system", 
                 source_system: str = None, original_error: Exception = None):
        self.source_system = source_system
        self.original_error = original_error
        message_with_source = f"{message} (System: {source_system})" if source_system else message
        super().__init__(message_with_source)


class EntityNotFoundError(AdapterError):
    """Exception raised when an entity is not found."""
    def __init__(self, entity_type: str, entity_id: str, source_system: str = None):
        message = f"{entity_type.capitalize()} with ID '{entity_id}' not found"
        super().__init__(message, source_system)
        self.entity_type = entity_type
        self.entity_id = entity_id


class ValidationError(MiddlewareError):
    """Exception raised when validation fails."""
    def __init__(self, message: str = "Validation error", errors: dict = None):
        self.errors = errors or {}
        super().__init__(message)


class ConfigurationError(MiddlewareError):
    """Exception raised when there's a configuration error."""
    pass


class ConversionError(MiddlewareError):
    """Exception raised when data conversion fails."""
    def __init__(self, message: str = "Error converting data", 
                 source_system: str = None, target_format: str = None):
        self.source_system = source_system
        self.target_format = target_format
        details = []
        if source_system:
            details.append(f"source: {source_system}")
        if target_format:
            details.append(f"target format: {target_format}")
        
        message_with_details = f"{message} ({', '.join(details)})" if details else message
        super().__init__(message_with_details)


class AuthenticationError(AdapterError):
    """Exception raised when authentication with an external system fails."""
    def __init__(self, message: str = "Authentication failed", source_system: str = None):
        super().__init__(message, source_system)


class RateLimitError(AdapterError):
    """Exception raised when a rate limit is hit."""
    def __init__(self, message: str = "Rate limit exceeded", 
                 source_system: str = None, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, source_system) 