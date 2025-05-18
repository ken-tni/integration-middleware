import sys
import logging
from pathlib import Path
from loguru import logger
from app.config.settings import settings

# Configure loguru logger
def setup_logging():
    """Configure logging for the application."""
    # Remove default handlers
    logger.remove()
    
    # Determine log level from settings
    log_level = settings.LOG_LEVEL.upper()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for errors and above
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        log_path / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for all logs
    logger.add(
        log_path / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="3 days",
    )
    
    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Configure standard library logging to use loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Log startup message
    logger.info(f"Logging configured with level: {log_level}")
    logger.debug(f"Debug logging enabled")


def get_logger(name: str):
    """Get a logger for a specific module.
    
    Args:
        name: The name of the module
        
    Returns:
        A logger instance
    """
    return logger.bind(name=name) 