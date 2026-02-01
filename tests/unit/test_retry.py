"""
Unit tests for the Retry & Backoff Handler.
"""


import pytest

from data_loader.retry import (
    RetryConfig,
    RetryError,
    RetryHandler,
    RetryStats,
    retry_with_backoff,
    with_retry,
)


@pytest.mark.unit
class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.5

    def test_custom_values(self):
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            jitter=False,
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.jitter is False

    def test_non_retryable_status_codes(self):
        config = RetryConfig()
        assert 400 in config.non_retryable_status_codes
        assert 401 in config.non_retryable_status_codes
        assert 403 in config.non_retryable_status_codes
        assert 404 in config.non_retryable_status_codes


@pytest.mark.unit
class TestRetryStats:
    """Tests for RetryStats dataclass."""

    def test_default_values(self):
        stats = RetryStats()
        assert stats.total_attempts == 0
        assert stats.successful_attempts == 0
        assert stats.failed_attempts == 0
        assert stats.retries_performed == 0

    def test_to_dict(self):
        stats = RetryStats(
            total_attempts=10,
            successful_attempts=8,
            failed_attempts=2,
            retries_performed=5,
            total_delay_seconds=12.567,
        )
        d = stats.to_dict()
        assert d["total_attempts"] == 10
        assert d["total_delay_seconds"] == 12.57  # Rounded


@pytest.mark.unit
class TestRetryError:
    """Tests for RetryError exception."""

    def test_error_attributes(self):
        original_error = ValueError("Original")
        error = RetryError(
            "All retries failed",
            last_exception=original_error,
            attempts=4,
        )
        assert str(error) == "All retries failed"
        assert error.last_exception is original_error
        assert error.attempts == 4


@pytest.mark.unit
class TestRetryHandler:
    """Tests for RetryHandler class."""

    def test_init_default_config(self):
        handler = RetryHandler()
        assert handler.config.max_retries == 3

    def test_init_custom_config(self):
        config = RetryConfig(max_retries=5)
        handler = RetryHandler(config)
        assert handler.config.max_retries == 5

    def test_calculate_delay_exponential(self):
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        handler = RetryHandler(config)

        assert handler.calculate_delay(0) == 1.0
        assert handler.calculate_delay(1) == 2.0
        assert handler.calculate_delay(2) == 4.0
        assert handler.calculate_delay(3) == 8.0

    def test_calculate_delay_caps_at_max(self):
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False,
        )
        handler = RetryHandler(config)

        assert handler.calculate_delay(10) == 5.0  # Should be capped

    def test_calculate_delay_with_jitter(self):
        config = RetryConfig(
            base_delay=1.0,
            jitter=True,
            jitter_factor=0.5,
        )
        handler = RetryHandler(config)

        # With jitter, delay should vary
        delays = [handler.calculate_delay(0) for _ in range(10)]
        # Not all delays should be the same
        assert len(set(delays)) > 1
        # All should be within expected range (0.5 to 1.5 for base_delay=1.0)
        for delay in delays:
            assert 0.1 <= delay <= 1.5

    def test_should_retry_within_max(self):
        config = RetryConfig(max_retries=3)
        handler = RetryHandler(config)

        assert handler.should_retry(ValueError(), attempt=0) is True
        assert handler.should_retry(ValueError(), attempt=1) is True
        assert handler.should_retry(ValueError(), attempt=2) is True
        assert handler.should_retry(ValueError(), attempt=3) is False

    def test_should_retry_specific_exceptions(self):
        config = RetryConfig(
            retryable_exceptions=(ValueError, ConnectionError),
        )
        handler = RetryHandler(config)

        assert handler.should_retry(ValueError(), attempt=0) is True
        assert handler.should_retry(ConnectionError(), attempt=0) is True
        assert handler.should_retry(TypeError(), attempt=0) is False

    def test_should_not_retry_non_retryable_status(self):
        config = RetryConfig(
            non_retryable_status_codes=(400, 401, 404),
        )
        handler = RetryHandler(config)

        class HttpError(Exception):
            def __init__(self, status_code):
                self.status_code = status_code

        assert handler.should_retry(HttpError(400), attempt=0) is False
        assert handler.should_retry(HttpError(401), attempt=0) is False
        assert handler.should_retry(HttpError(404), attempt=0) is False
        assert handler.should_retry(HttpError(500), attempt=0) is True
        assert handler.should_retry(HttpError(503), attempt=0) is True

    @pytest.mark.asyncio
    async def test_execute_success_first_try(self):
        handler = RetryHandler()

        async def success():
            return "result"

        result = await handler.execute(success)
        assert result == "result"

        stats = handler.get_stats()
        assert stats.total_attempts == 1
        assert stats.successful_attempts == 1
        assert stats.retries_performed == 0

    @pytest.mark.asyncio
    async def test_execute_success_after_retries(self):
        config = RetryConfig(base_delay=0.01, jitter=False)
        handler = RetryHandler(config)

        call_count = 0

        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await handler.execute(fails_twice)
        assert result == "success"
        assert call_count == 3

        stats = handler.get_stats()
        assert stats.total_attempts == 3
        assert stats.successful_attempts == 1
        assert stats.retries_performed == 2

    @pytest.mark.asyncio
    async def test_execute_exhausts_retries(self):
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        handler = RetryHandler(config)

        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            await handler.execute(always_fails)

        assert exc_info.value.attempts == 3  # Initial + 2 retries
        assert isinstance(exc_info.value.last_exception, ValueError)

        stats = handler.get_stats()
        assert stats.total_attempts == 3
        assert stats.failed_attempts == 1
        assert stats.retries_performed == 2

    @pytest.mark.asyncio
    async def test_execute_no_retry_on_non_retryable(self):
        config = RetryConfig(
            retryable_exceptions=(ConnectionError,),
            base_delay=0.01,
        )
        handler = RetryHandler(config)

        async def raises_value_error():
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await handler.execute(raises_value_error)

        stats = handler.get_stats()
        assert stats.total_attempts == 1
        assert stats.retries_performed == 0

    @pytest.mark.asyncio
    async def test_execute_with_args_and_kwargs(self):
        handler = RetryHandler()

        async def add(a, b, multiplier=1):
            return (a + b) * multiplier

        result = await handler.execute(add, 2, 3, multiplier=2)
        assert result == 10

    def test_reset_stats(self):
        handler = RetryHandler()
        handler._stats.total_attempts = 100
        handler._stats.retries_performed = 50

        handler.reset_stats()

        stats = handler.get_stats()
        assert stats.total_attempts == 0
        assert stats.retries_performed == 0


@pytest.mark.unit
class TestRetryDecorator:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        @with_retry(max_retries=3)
        async def my_func():
            return "decorated"

        result = await my_func()
        assert result == "decorated"

    @pytest.mark.asyncio
    async def test_decorator_with_retries(self):
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_exhausts_retries(self):
        @with_retry(max_retries=2, base_delay=0.01)
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryError):
            await always_fails()


@pytest.mark.unit
class TestRetryWithBackoff:
    """Tests for retry_with_backoff convenience function."""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        async def success():
            return "result"

        result = await retry_with_backoff(success)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_retry_with_args(self):
        async def add(a, b):
            return a + b

        result = await retry_with_backoff(add, 5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_retry_custom_config(self):
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError()
            return "ok"

        result = await retry_with_backoff(
            flaky,
            max_retries=5,
            base_delay=0.01,
        )
        assert result == "ok"
        assert call_count == 3


@pytest.mark.unit
class TestRetryTiming:
    """Tests for retry timing behavior."""

    @pytest.mark.asyncio
    async def test_delays_accumulate(self):
        import time

        config = RetryConfig(
            max_retries=2,
            base_delay=0.05,
            exponential_base=2.0,
            jitter=False,
        )
        handler = RetryHandler(config)

        async def always_fails():
            raise ValueError()

        start = time.perf_counter()
        with pytest.raises(RetryError):
            await handler.execute(always_fails)
        elapsed = time.perf_counter() - start

        # Should have delayed: 0.05 + 0.1 = 0.15 seconds minimum
        assert elapsed >= 0.14  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_jitter_varies_delays(self):
        config = RetryConfig(
            max_retries=5,
            base_delay=0.01,
            jitter=True,
            jitter_factor=0.5,
        )
        handler1 = RetryHandler(config)
        handler2 = RetryHandler(config)

        # Calculate multiple delays
        delays1 = [handler1.calculate_delay(i) for i in range(5)]
        delays2 = [handler2.calculate_delay(i) for i in range(5)]

        # With jitter, the delays should differ between handlers
        # (statistically very unlikely to be identical)
        assert delays1 != delays2
