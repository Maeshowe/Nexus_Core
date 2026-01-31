"""
OmniData Nexus Core - Circuit Breaker

Implements the Circuit Breaker pattern for failure isolation and recovery.
Prevents cascading failures by failing fast when a service is unhealthy.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast, not allowing requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker prevents request execution."""

    def __init__(self, message: str, state: CircuitState, provider: str):
        super().__init__(message)
        self.state = state
        self.provider = provider


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    error_threshold: float = 0.2  # 20% error rate triggers open
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    min_requests: int = 10  # Minimum requests before evaluating
    half_open_max_requests: int = 3  # Requests to allow in half-open state
    window_size: int = 100  # Rolling window size for tracking


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker."""

    state: CircuitState
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    last_failure_time: Optional[float]
    last_state_change: Optional[float]
    consecutive_successes: int
    time_in_current_state: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "error_rate": round(self.error_rate, 4),
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "consecutive_successes": self.consecutive_successes,
            "time_in_current_state": round(self.time_in_current_state, 2),
        }


class CircuitBreaker:
    """
    Circuit breaker for a single provider.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Error threshold exceeded, requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Transitions:
    - CLOSED -> OPEN: When error rate exceeds threshold
    - OPEN -> HALF_OPEN: After recovery timeout expires
    - HALF_OPEN -> CLOSED: On successful requests
    - HALF_OPEN -> OPEN: On failed request
    """

    def __init__(
        self,
        provider: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            provider: Provider name
            config: Optional configuration
        """
        self.provider = provider
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._lock = Lock()

        # Request tracking (rolling window)
        self._requests: deque = deque(maxlen=self.config.window_size)

        # State tracking
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.time()
        self._consecutive_successes: int = 0
        self._half_open_requests: int = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def _check_state_transition(self) -> None:
        """Check and perform automatic state transitions."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: Target state
        """
        if self._state != new_state:
            self._state = new_state
            self._last_state_change = time.time()

            if new_state == CircuitState.HALF_OPEN:
                self._half_open_requests = 0
                self._consecutive_successes = 0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent requests."""
        if len(self._requests) == 0:
            return 0.0

        failures = sum(1 for success in self._requests if not success)
        return failures / len(self._requests)

    def can_execute(self) -> bool:
        """
        Check if a request can be executed.

        Returns:
            True if request is allowed
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                return False

            if self._state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                return self._half_open_requests < self.config.half_open_max_requests

        return False

    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            self._requests.append(True)
            self._consecutive_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_requests += 1

                # Transition to closed after enough successes
                if self._consecutive_successes >= self.config.half_open_max_requests:
                    self._transition_to(CircuitState.CLOSED)

    def record_failure(self) -> None:
        """Record a failed request."""
        with self._lock:
            self._requests.append(False)
            self._last_failure_time = time.time()
            self._consecutive_successes = 0

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to(CircuitState.OPEN)
                return

            if self._state == CircuitState.CLOSED:
                # Check if we should open
                if len(self._requests) >= self.config.min_requests:
                    error_rate = self._calculate_error_rate()
                    if error_rate >= self.config.error_threshold:
                        self._transition_to(CircuitState.OPEN)

    def get_stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        with self._lock:
            self._check_state_transition()

            total = len(self._requests)
            successes = sum(1 for s in self._requests if s)
            failures = total - successes
            error_rate = failures / total if total > 0 else 0.0

            return CircuitBreakerStats(
                state=self._state,
                total_requests=total,
                successful_requests=successes,
                failed_requests=failures,
                error_rate=error_rate,
                last_failure_time=self._last_failure_time,
                last_state_change=self._last_state_change,
                consecutive_successes=self._consecutive_successes,
                time_in_current_state=time.time() - self._last_state_change,
            )

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._requests.clear()
            self._last_failure_time = None
            self._last_state_change = time.time()
            self._consecutive_successes = 0
            self._half_open_requests = 0

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        if not self.can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker is {self._state.value} for {self.provider}",
                state=self._state,
                provider=self.provider,
            )

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


class CircuitBreakerManager:
    """
    Manages circuit breakers for all providers.

    Provides a centralized interface for circuit breaker management
    across multiple providers.

    Usage:
        manager = CircuitBreakerManager()

        # Execute with circuit breaker protection
        try:
            result = await manager.execute("fmp", api_call)
        except CircuitBreakerError:
            # Circuit is open, handle gracefully
            pass

        # Or check manually
        if manager.can_execute("fmp"):
            result = await api_call()
            manager.record_success("fmp")
    """

    def __init__(
        self,
        default_config: Optional[CircuitBreakerConfig] = None,
        provider_configs: Optional[dict[str, CircuitBreakerConfig]] = None,
    ):
        """
        Initialize circuit breaker manager.

        Args:
            default_config: Default configuration for all providers
            provider_configs: Provider-specific configurations
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self.provider_configs = provider_configs or {}

        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def _get_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for a provider."""
        if provider not in self._breakers:
            with self._lock:
                if provider not in self._breakers:
                    config = self.provider_configs.get(provider, self.default_config)
                    self._breakers[provider] = CircuitBreaker(provider, config)

        return self._breakers[provider]

    def get_state(self, provider: str) -> CircuitState:
        """Get circuit state for a provider."""
        return self._get_breaker(provider).state

    def can_execute(self, provider: str) -> bool:
        """Check if a request can be executed for a provider."""
        return self._get_breaker(provider).can_execute()

    def record_success(self, provider: str) -> None:
        """Record a successful request for a provider."""
        self._get_breaker(provider).record_success()

    def record_failure(self, provider: str) -> None:
        """Record a failed request for a provider."""
        self._get_breaker(provider).record_failure()

    async def execute(
        self,
        provider: str,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            provider: Provider name
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        return await self._get_breaker(provider).execute(func, *args, **kwargs)

    def get_stats(self, provider: Optional[str] = None) -> dict:
        """
        Get circuit breaker statistics.

        Args:
            provider: Optional provider to get stats for

        Returns:
            Statistics dictionary
        """
        if provider:
            return self._get_breaker(provider).get_stats().to_dict()

        return {
            p: self._get_breaker(p).get_stats().to_dict()
            for p in list(self._breakers.keys()) or ["fmp", "polygon", "fred"]
        }

    def reset(self, provider: Optional[str] = None) -> None:
        """
        Reset circuit breaker(s).

        Args:
            provider: Optional provider to reset, or None for all
        """
        if provider:
            if provider in self._breakers:
                self._breakers[provider].reset()
        else:
            for breaker in self._breakers.values():
                breaker.reset()

    def get_all_states(self) -> dict[str, CircuitState]:
        """Get states for all tracked providers."""
        return {
            provider: breaker.state
            for provider, breaker in self._breakers.items()
        }

    def is_healthy(self, provider: str) -> bool:
        """Check if a provider's circuit breaker is healthy (closed)."""
        return self._get_breaker(provider).is_closed
