"""
OmniData Nexus Core - Retry & Backoff Handler

Implements exponential backoff with jitter for transient failure recovery.
"""

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay between retries
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add randomness to delays
    jitter_factor: float = 0.5  # Jitter range (0.5 = ±50% of delay)

    # Retryable exceptions (if empty, all exceptions are retried)
    retryable_exceptions: tuple = field(default_factory=tuple)

    # Non-retryable status codes (e.g., 400, 401, 403, 404)
    non_retryable_status_codes: tuple = field(
        default_factory=lambda: (400, 401, 403, 404)
    )


@dataclass
class RetryStats:
    """Statistics for retry operations."""

    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    retries_performed: int = 0
    total_delay_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "failed_attempts": self.failed_attempts,
            "retries_performed": self.retries_performed,
            "total_delay_seconds": round(self.total_delay_seconds, 2),
        }


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        last_exception: Optional[Exception] = None,
        attempts: int = 0,
    ):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


class RetryHandler:
    """
    Handles retry logic with exponential backoff and jitter.

    Features:
    - Configurable max retries
    - Exponential backoff with customizable base
    - Jitter to prevent thundering herd
    - Exception filtering (only retry specific exceptions)
    - Status code filtering (don't retry client errors)

    Usage:
        handler = RetryHandler()

        # Execute with retry
        result = await handler.execute(api_call)

        # Or with decorator-like usage
        async def my_api_call():
            return await make_request()

        result = await handler.execute(my_api_call)
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
    ):
        """
        Initialize retry handler.

        Args:
            config: Optional retry configuration
        """
        self.config = config or RetryConfig()
        self._stats = RetryStats()

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.

        Uses exponential backoff: delay = base * (exponential_base ^ attempt)
        With optional jitter: delay * (1 ± jitter_factor)

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter if enabled
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Minimum 100ms

        return delay

    def _is_exception_retryable(self, exception: Exception) -> bool:
        """
        Check if an exception type is retryable.

        Args:
            exception: The exception that occurred

        Returns:
            True if exception type is retryable
        """
        # Check if exception is in retryable list
        if self.config.retryable_exceptions:
            if not isinstance(exception, self.config.retryable_exceptions):
                return False

        # Check for non-retryable status codes
        status_code = getattr(exception, 'status_code', None)
        return not (status_code and status_code in self.config.non_retryable_status_codes)

    def should_retry(
        self,
        exception: Exception,
        attempt: int,
    ) -> bool:
        """
        Determine if a failed request should be retried.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number

        Returns:
            True if should retry
        """
        # Check max retries
        if attempt >= self.config.max_retries:
            return False

        # Check if exception type is retryable
        return self._is_exception_retryable(exception)

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RetryError: If all retries are exhausted
        """
        last_exception: Optional[Exception] = None
        total_delay = 0.0

        for attempt in range(self.config.max_retries + 1):
            self._stats.total_attempts += 1

            try:
                result = await func(*args, **kwargs)
                self._stats.successful_attempts += 1
                return result

            except Exception as e:
                last_exception = e

                # Check if this exception type is retryable
                is_exception_retryable = self._is_exception_retryable(e)

                if not is_exception_retryable:
                    # Non-retryable exception type - fail immediately
                    self._stats.failed_attempts += 1
                    raise

                # Check if we have retries left
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    total_delay += delay
                    self._stats.retries_performed += 1
                    self._stats.total_delay_seconds += delay

                    await asyncio.sleep(delay)
                # else: last attempt failed, will exit loop

        # All retries exhausted
        self._stats.failed_attempts += 1
        raise RetryError(
            f"All {self.config.max_retries + 1} attempts failed",
            last_exception=last_exception,
            attempts=self.config.max_retries + 1,
        )

    def get_stats(self) -> RetryStats:
        """Get retry statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = RetryStats()


class RetryContext:
    """
    Context manager for retry operations.

    Provides a clean interface for wrapping code blocks with retry logic.

    Usage:
        handler = RetryHandler()

        async with handler.context() as ctx:
            result = await api_call()
            ctx.set_result(result)
    """

    def __init__(self, handler: RetryHandler):
        self.handler = handler
        self._result: Any = None
        self._exception: Optional[Exception] = None

    def set_result(self, result: Any) -> None:
        """Set the successful result."""
        self._result = result

    def get_result(self) -> Any:
        """Get the result."""
        return self._result

    async def __aenter__(self) -> "RetryContext":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is not None:
            self._exception = exc_val
            # Let the exception propagate for the handler to catch
            return False
        return False


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[Sequence[type[Exception]]] = None,
):
    """
    Decorator for adding retry logic to async functions.

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        retryable_exceptions: Exceptions to retry on

    Usage:
        @with_retry(max_retries=3)
        async def my_api_call():
            return await make_request()
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=tuple(retryable_exceptions or []),
            )
            handler = RetryHandler(config)
            return await handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# Convenience functions for common patterns
async def retry_with_backoff(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs,
) -> T:
    """
    Execute a function with retry and exponential backoff.

    Args:
        func: Async function to execute
        *args: Positional arguments
        max_retries: Maximum retries
        base_delay: Base delay in seconds
        **kwargs: Keyword arguments

    Returns:
        Function result
    """
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    handler = RetryHandler(config)
    return await handler.execute(func, *args, **kwargs)
