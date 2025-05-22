print("main.py is running")
import uvicorn
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.utils.exception_handlers import setup_exception_handlers
from app.core.middleware import AuthenticationMiddleware

setup_logging()  # Ensure logging is set up first
from app.core.adapter_factory import adapter_factory  # Import after logging


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="System B - Integration Middleware",
        description="Middleware system that standardizes data from System A for System C",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Setup middleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix="/api")
    
    return app

app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    ) 