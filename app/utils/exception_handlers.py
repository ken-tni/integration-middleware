from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import (
    MiddlewareError, 
    AdapterError, 
    EntityNotFoundError, 
    ValidationError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError
)
from app.utils.logging import get_logger

logger = get_logger("exception_handlers")


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the application.
    
    Args:
        app: The FastAPI application
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors from FastAPI/Pydantic."""
        logger.warning(f"Request validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,  # HTTP_422_UNPROCESSABLE_ENTITY
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )
    
    @app.exception_handler(ValidationError)
    async def custom_validation_exception_handler(request: Request, exc: ValidationError):
        """Handle custom validation errors."""
        logger.warning(f"Validation error: {exc.message} - {exc.errors}")
        return JSONResponse(
            status_code=422,  # HTTP_422_UNPROCESSABLE_ENTITY
            content={
                "detail": exc.message,
                "errors": exc.errors,
            },
        )
    
    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundError):
        """Handle entity not found errors."""
        logger.info(f"Entity not found: {exc.message}")
        return JSONResponse(
            status_code=404,  # HTTP_404_NOT_FOUND
            content={"detail": exc.message},
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors."""
        logger.error(f"Authentication error: {exc.message}")
        return JSONResponse(
            status_code=401,  # HTTP_401_UNAUTHORIZED
            content={"detail": "Authentication failed"},
        )
    
    @app.exception_handler(RateLimitError)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
        """Handle rate limit errors."""
        logger.warning(f"Rate limit exceeded: {exc.message}")
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=429,  # HTTP_429_TOO_MANY_REQUESTS
            content={"detail": exc.message},
            headers=headers,
        )
    
    @app.exception_handler(AdapterError)
    async def adapter_exception_handler(request: Request, exc: AdapterError):
        """Handle adapter errors."""
        logger.error(f"Adapter error: {exc.message}", exc_info=exc.original_error)
        return JSONResponse(
            status_code=502,  # HTTP_502_BAD_GATEWAY
            content={"detail": "Error communicating with external system"},
        )
    
    @app.exception_handler(ConfigurationError)
    async def configuration_exception_handler(request: Request, exc: ConfigurationError):
        """Handle configuration errors."""
        logger.error(f"Configuration error: {exc.message}")
        return JSONResponse(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            content={"detail": "Internal server error"},
        )
    
    @app.exception_handler(MiddlewareError)
    async def middleware_exception_handler(request: Request, exc: MiddlewareError):
        """Handle generic middleware errors."""
        logger.error(f"Middleware error: {exc.message}")
        return JSONResponse(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            content={"detail": "Internal server error"},
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions."""
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            content={"detail": "Internal server error"},
        ) 