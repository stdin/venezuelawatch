"""
Utility functions for data ingestion tasks.

Provides:
- Retry strategies with exponential backoff
- Rate limiting
- Logging utilities
"""
import time
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import Callable, Any

logger = logging.getLogger(__name__)


def configure_retry_strategy(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    multiplier: int = 2,
):
    """
    Create a Tenacity retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        multiplier: Multiplier for exponential backoff

    Returns:
        Tenacity retry decorator

    Example:
        @configure_retry_strategy(max_attempts=3)
        def fetch_api_data():
            # API call here
            pass
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )


class RateLimiter:
    """
    Token bucket rate limiter.

    Limits the rate of API calls to avoid hitting rate limits.
    Uses a simple token bucket algorithm.
    """

    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def wait_if_needed(self):
        """
        Wait if rate limit would be exceeded.

        Blocks until enough time has passed to make another call.
        """
        now = time.time()

        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

        # If at limit, wait until oldest call expires
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Clean up expired calls again after sleeping
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

        # Record this call
        self.calls.append(now)

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to rate limit a function.

        Args:
            func: Function to rate limit

        Returns:
            Wrapped function that respects rate limit
        """
        def wrapper(*args, **kwargs) -> Any:
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper


def log_ingestion_event(
    source: str,
    event_type: str,
    count: int,
    duration: float = None,
    error: str = None,
):
    """
    Log an ingestion event for monitoring and debugging.

    Args:
        source: Data source name (e.g., 'gdelt', 'fred')
        event_type: Type of event (e.g., 'success', 'failure', 'partial')
        count: Number of records processed
        duration: Time taken in seconds (optional)
        error: Error message if applicable (optional)
    """
    log_data = {
        'source': source,
        'event_type': event_type,
        'count': count,
    }

    if duration is not None:
        log_data['duration'] = duration

    if error:
        logger.error(
            f"Ingestion event: {source} {event_type}",
            extra=log_data,
            exc_info=error if isinstance(error, Exception) else None
        )
    else:
        logger.info(
            f"Ingestion event: {source} {event_type} - {count} records",
            extra=log_data
        )
