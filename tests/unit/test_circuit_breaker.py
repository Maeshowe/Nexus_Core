"""
Unit tests for the Circuit Breaker.
"""

import time
from unittest.mock import patch

import pytest

from data_loader.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitBreakerStats,
    CircuitState,
)


@pytest.mark.unit
class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_all_states(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


@pytest.mark.unit
class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_default_values(self):
        config = CircuitBreakerConfig()
        assert config.error_threshold == 0.2
        assert config.recovery_timeout == 60.0
        assert config.min_requests == 10
        assert config.half_open_max_requests == 3
        assert config.window_size == 100

    def test_custom_values(self):
        config = CircuitBreakerConfig(
            error_threshold=0.3,
            recovery_timeout=30.0,
            min_requests=5,
        )
        assert config.error_threshold == 0.3
        assert config.recovery_timeout == 30.0
        assert config.min_requests == 5


@pytest.mark.unit
class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats dataclass."""

    def test_to_dict(self):
        stats = CircuitBreakerStats(
            state=CircuitState.CLOSED,
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            error_rate=0.1,
            last_failure_time=1234567890.0,
            last_state_change=1234567800.0,
            consecutive_successes=5,
            time_in_current_state=90.0,
        )
        d = stats.to_dict()

        assert d["state"] == "closed"
        assert d["total_requests"] == 100
        assert d["error_rate"] == 0.1


@pytest.mark.unit
class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker("fmp")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True
        assert cb.is_open is False
        assert cb.is_half_open is False

    def test_can_execute_when_closed(self):
        cb = CircuitBreaker("fmp")
        assert cb.can_execute() is True

    def test_record_success(self):
        cb = CircuitBreaker("fmp")
        cb.record_success()
        stats = cb.get_stats()
        assert stats.successful_requests == 1
        assert stats.failed_requests == 0

    def test_record_failure(self):
        cb = CircuitBreaker("fmp")
        cb.record_failure()
        stats = cb.get_stats()
        assert stats.failed_requests == 1
        assert stats.successful_requests == 0

    def test_stays_closed_below_threshold(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=10,
        )
        cb = CircuitBreaker("fmp", config)

        # 9 successes, 1 failure = 10% error rate (below 20%)
        for _ in range(9):
            cb.record_success()
        cb.record_failure()

        assert cb.state == CircuitState.CLOSED

    def test_opens_at_threshold(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=10,
        )
        cb = CircuitBreaker("fmp", config)

        # 8 successes, 2 failures = 20% error rate (at threshold)
        for _ in range(8):
            cb.record_success()
        for _ in range(2):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_opens_above_threshold(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=10,
        )
        cb = CircuitBreaker("fmp", config)

        # 7 successes, 3 failures = 30% error rate
        for _ in range(7):
            cb.record_success()
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_does_not_open_below_min_requests(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=10,
        )
        cb = CircuitBreaker("fmp", config)

        # 5 failures out of 5 = 100% error rate, but below min_requests
        for _ in range(5):
            cb.record_failure()

        assert cb.state == CircuitState.CLOSED

    def test_cannot_execute_when_open(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
        )
        cb = CircuitBreaker("fmp", config)

        # Force open state
        for _ in range(3):
            cb.record_success()
        for _ in range(2):
            cb.record_failure()  # 40% error rate

        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_transitions_to_half_open_after_timeout(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
            recovery_timeout=0.1,  # 100ms for testing
        )
        cb = CircuitBreaker("fmp", config)

        # Force open state
        for _ in range(3):
            cb.record_success()
        for _ in range(2):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # State should transition to half-open
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_limited_requests(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
            recovery_timeout=0.01,
            half_open_max_requests=3,
        )
        cb = CircuitBreaker("fmp", config)

        # Force to half-open
        for _ in range(5):
            cb.record_failure()
        time.sleep(0.02)

        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True

    def test_half_open_closes_after_successes(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
            recovery_timeout=0.01,
            half_open_max_requests=3,
        )
        cb = CircuitBreaker("fmp", config)

        # Force to half-open
        for _ in range(5):
            cb.record_failure()
        time.sleep(0.02)

        assert cb.state == CircuitState.HALF_OPEN

        # Record enough successes
        for _ in range(3):
            cb.record_success()

        assert cb.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
            recovery_timeout=0.01,
            half_open_max_requests=3,
        )
        cb = CircuitBreaker("fmp", config)

        # Force to half-open
        for _ in range(5):
            cb.record_failure()
        time.sleep(0.02)

        assert cb.state == CircuitState.HALF_OPEN

        # Any failure in half-open goes back to open
        cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
        )
        cb = CircuitBreaker("fmp", config)

        # Force open state
        for _ in range(5):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

        cb.reset()

        assert cb.state == CircuitState.CLOSED
        stats = cb.get_stats()
        assert stats.total_requests == 0

    @pytest.mark.asyncio
    async def test_execute_success(self):
        cb = CircuitBreaker("fmp")

        async def success_func():
            return "success"

        result = await cb.execute(success_func)
        assert result == "success"

        stats = cb.get_stats()
        assert stats.successful_requests == 1

    @pytest.mark.asyncio
    async def test_execute_failure_records_failure(self):
        cb = CircuitBreaker("fmp")

        async def failing_func():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb.execute(failing_func)

        stats = cb.get_stats()
        assert stats.failed_requests == 1

    @pytest.mark.asyncio
    async def test_execute_raises_when_open(self):
        config = CircuitBreakerConfig(
            error_threshold=0.2,
            min_requests=5,
        )
        cb = CircuitBreaker("fmp", config)

        # Force open
        for _ in range(5):
            cb.record_failure()

        async def should_not_run():
            return "never"

        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.execute(should_not_run)

        assert exc_info.value.state == CircuitState.OPEN
        assert exc_info.value.provider == "fmp"


@pytest.mark.unit
class TestCircuitBreakerError:
    """Tests for CircuitBreakerError exception."""

    def test_error_attributes(self):
        error = CircuitBreakerError(
            "Circuit is open",
            state=CircuitState.OPEN,
            provider="fmp",
        )
        assert str(error) == "Circuit is open"
        assert error.state == CircuitState.OPEN
        assert error.provider == "fmp"


@pytest.mark.unit
class TestCircuitBreakerManager:
    """Tests for CircuitBreakerManager class."""

    def test_init_default_config(self):
        manager = CircuitBreakerManager()
        # Should create breakers on demand
        assert manager.get_state("fmp") == CircuitState.CLOSED

    def test_init_custom_config(self):
        config = CircuitBreakerConfig(error_threshold=0.5)
        manager = CircuitBreakerManager(default_config=config)
        # The custom config should be used
        assert manager.default_config.error_threshold == 0.5

    def test_provider_specific_config(self):
        fmp_config = CircuitBreakerConfig(error_threshold=0.1)
        manager = CircuitBreakerManager(
            provider_configs={"fmp": fmp_config}
        )
        # Force creation of breaker
        manager.record_success("fmp")
        # The provider-specific config should be used
        stats = manager.get_stats("fmp")
        assert stats is not None

    def test_can_execute(self):
        manager = CircuitBreakerManager()
        assert manager.can_execute("fmp") is True

    def test_record_success(self):
        manager = CircuitBreakerManager()
        manager.record_success("fmp")
        stats = manager.get_stats("fmp")
        assert stats["successful_requests"] == 1

    def test_record_failure(self):
        manager = CircuitBreakerManager()
        manager.record_failure("fmp")
        stats = manager.get_stats("fmp")
        assert stats["failed_requests"] == 1

    @pytest.mark.asyncio
    async def test_execute_success(self):
        manager = CircuitBreakerManager()

        async def api_call():
            return {"data": "result"}

        result = await manager.execute("fmp", api_call)
        assert result == {"data": "result"}

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        manager = CircuitBreakerManager()

        async def failing_call():
            raise ValueError("API error")

        with pytest.raises(ValueError):
            await manager.execute("fmp", failing_call)

    def test_get_all_states(self):
        manager = CircuitBreakerManager()
        manager.record_success("fmp")
        manager.record_success("polygon")

        states = manager.get_all_states()
        assert "fmp" in states
        assert "polygon" in states
        assert states["fmp"] == CircuitState.CLOSED

    def test_reset_single_provider(self):
        config = CircuitBreakerConfig(min_requests=5)
        manager = CircuitBreakerManager(default_config=config)

        for _ in range(5):
            manager.record_failure("fmp")
            manager.record_failure("polygon")

        assert manager.get_state("fmp") == CircuitState.OPEN
        assert manager.get_state("polygon") == CircuitState.OPEN

        manager.reset("fmp")

        assert manager.get_state("fmp") == CircuitState.CLOSED
        assert manager.get_state("polygon") == CircuitState.OPEN

    def test_reset_all_providers(self):
        config = CircuitBreakerConfig(min_requests=5)
        manager = CircuitBreakerManager(default_config=config)

        for _ in range(5):
            manager.record_failure("fmp")
            manager.record_failure("polygon")

        manager.reset()

        assert manager.get_state("fmp") == CircuitState.CLOSED
        assert manager.get_state("polygon") == CircuitState.CLOSED

    def test_is_healthy(self):
        config = CircuitBreakerConfig(min_requests=5)
        manager = CircuitBreakerManager(default_config=config)

        assert manager.is_healthy("fmp") is True

        for _ in range(5):
            manager.record_failure("fmp")

        assert manager.is_healthy("fmp") is False

    def test_independent_providers(self):
        """Verify that different providers have independent circuit breakers."""
        config = CircuitBreakerConfig(min_requests=5)
        manager = CircuitBreakerManager(default_config=config)

        # Fail FMP
        for _ in range(5):
            manager.record_failure("fmp")

        # Polygon should still be healthy
        assert manager.get_state("fmp") == CircuitState.OPEN
        assert manager.get_state("polygon") == CircuitState.CLOSED
        assert manager.can_execute("polygon") is True
