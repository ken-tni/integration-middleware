from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)
from app.config.settings import settings
from app.core.exceptions import AdapterError, RateLimitError
from app.utils.logging import get_logger

logger = get_logger("retry")


def create_retry_decorator(
    max_attempts=None,
    min_wait=1,
    max_wait=30,
    retry_exceptions=(Exception,),
    exclude_exceptions=(),
):
    """Create a retry decorator with custom settings.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_exceptions: Tuple of exceptions that should trigger a retry
        exclude_exceptions: Tuple of exceptions that should not trigger a retry
        
    Returns:
        A retry decorator
    """
    if max_attempts is None:
        max_attempts = settings.MAX_RETRIES
    
    def retry_logger(retry_state):
        if retry_state.attempt_number > 1:
            exception = retry_state.outcome.exception()
            logger.warning(
                f"Retry attempt {retry_state.attempt_number}/{max_attempts} "
                f"after exception: {exception.__class__.__name__}: {str(exception)}"
            )
    
    def should_retry(exception):
        # Don't retry if the exception is in the exclude list
        if isinstance(exception, exclude_exceptions):
            return False
        
        # Only retry if the exception is in the retry list
        return isinstance(exception, retry_exceptions)
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(should_retry),
        after=retry_logger,
        reraise=True,
    )


# Default retry decorator for adapter operations
adapter_retry = create_retry_decorator(
    retry_exceptions=(AdapterError,),
    exclude_exceptions=(RateLimitError,),
) 