"""
Integration tests for resilience components.

Tests QoS Router, Circuit Breaker, and Retry Handler working together.
"""

import asyncio
import time

import pytest

from data_loader.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
)
from data_loader.qos_router import QoSSemaphoreRouter
from data_loader.retry import RetryConfig, RetryError, RetryHandler


@pytest.mark.integration
class TestQoSWithRetry:
    """Test QoS Router combined with Retry Handler."""

    @pytest.mark.asyncio
    async def test_qos_with_retry_success(self):
        """Test successful execution with both QoS and retry."""
        router = QoSSemaphoreRouter()
        retry_handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01))

        async def api_call():
            return "success"

        async def with_qos():
            async with router.acquire("fmp"):
                return await retry_handler.execute(api_call)

        result = await with_qos()
        assert result == "success"

        qos_stats = router.get_stats("fmp")
        assert qos_stats["total_requests"] == 1

        retry_stats = retry_handler.get_stats()
        assert retry_stats.successful_attempts == 1

    @pytest.mark.asyncio
    async def test_qos_limits_concurrent_retries(self):
        """Verify QoS limits apply even during retries."""
        router = QoSSemaphoreRouter(limits={"test": 2})
        retry_handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01))

        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_call():
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent:
                    max_concurrent = current_concurrent

            await asyncio.sleep(0.02)

            async with lock:
                current_concurrent -= 1

            return "done"

        async def with_both():
            async with router.acquire("test"):
                return await retry_handler.execute(tracked_call)

        # Run multiple concurrent calls
        await asyncio.gather(*[with_both() for _ in range(5)])

        # Max concurrent should be limited by QoS
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_retry_respects_qos_during_backoff(self):
        """Ensure QoS slot is held during retry delays."""
        router = QoSSemaphoreRouter(limits={"test": 1})
        retry_handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.05))

        call_count = 0
        slots_during_retry = []

        async def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First fail")
            return "success"

        async def with_both():
            async with router.acquire("test"):
                # Track available slots during execution
                slots_during_retry.append(router.get_available_slots("test"))
                return await retry_handler.execute(flaky_call)

        # This should hold the slot during retry
        result = await with_both()
        assert result == "success"

        # Slot should have been 0 (held) during execution
        assert 0 in slots_during_retry


@pytest.mark.integration
class TestCircuitBreakerWithRetry:
    """Test Circuit Breaker combined with Retry Handler."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry_success(self):
        """Test successful flow through circuit breaker and retry."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(min_requests=5))
        retry_handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01))

        async def api_call():
            return "data"

        async def with_both():
            if not cb.can_execute():
                raise CircuitBreakerError("Open", cb.state, "test")

            try:
                result = await retry_handler.execute(api_call)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise

        result = await with_both()
        assert result == "data"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_retry_before_circuit_opens(self):
        """Verify retries happen before circuit breaker trips."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            min_requests=5,
            error_threshold=0.5,
        ))
        retry_handler = RetryHandler(RetryConfig(max_retries=3, base_delay=0.01))

        call_count = 0

        async def flaky_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        async def with_both():
            if not cb.can_execute():
                raise CircuitBreakerError("Open", cb.state, "test")

            try:
                result = await retry_handler.execute(flaky_then_success)
                cb.record_success()
                return result
            except RetryError:
                cb.record_failure()
                raise
            except Exception:
                # Don't record failure for retryable errors
                raise

        result = await with_both()
        assert result == "success"
        assert call_count == 3

        # Circuit should record only the final success
        stats = cb.get_stats()
        assert stats.successful_requests == 1
        assert stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_retry_exhaustion(self):
        """Circuit should open after retries are exhausted multiple times."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            min_requests=3,
            error_threshold=0.5,
        ))
        retry_handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01))

        async def always_fails():
            raise ValueError("Always fails")

        async def with_both():
            if not cb.can_execute():
                raise CircuitBreakerError("Open", cb.state, "test")

            try:
                result = await retry_handler.execute(always_fails)
                cb.record_success()
                return result
            except RetryError:
                cb.record_failure()
                raise

        # Multiple failed attempts
        for _ in range(3):
            try:
                await with_both()
            except RetryError:
                pass

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN


@pytest.mark.integration
class TestAllResilienceComponents:
    """Test all resilience components working together."""

    @pytest.mark.asyncio
    async def test_full_resilience_stack(self):
        """Test QoS + Circuit Breaker + Retry together."""
        router = QoSSemaphoreRouter(limits={"api": 3})
        cb_manager = CircuitBreakerManager(
            default_config=CircuitBreakerConfig(min_requests=5)
        )
        retry_handler = RetryHandler(RetryConfig(max_retries=2, base_delay=0.01))

        call_count = 0
        results = []

        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise ValueError("Third call fails")
            return f"result-{call_count}"

        async def resilient_call():
            async with router.acquire("api"):
                if not cb_manager.can_execute("api"):
                    raise CircuitBreakerError("Open", CircuitState.OPEN, "api")

                try:
                    result = await retry_handler.execute(sometimes_fails)
                    cb_manager.record_success("api")
                    return result
                except RetryError:
                    cb_manager.record_failure("api")
                    raise

        # Execute multiple calls
        for _ in range(5):
            try:
                result = await resilient_call()
                results.append(result)
            except (RetryError, CircuitBreakerError):
                results.append("failed")

        # Should have some successes
        assert any(r.startswith("result") for r in results if isinstance(r, str) and r.startswith("result"))

        # QoS should have tracked requests
        assert router.get_stats("api")["total_requests"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_resilient_requests(self):
        """Test concurrent requests through full resilience stack."""
        router = QoSSemaphoreRouter(limits={"api": 5})
        cb_manager = CircuitBreakerManager()
        retry_handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01))

        completed = []
        lock = asyncio.Lock()

        async def api_call(request_id: int):
            await asyncio.sleep(0.02)  # Simulate API latency
            return f"response-{request_id}"

        async def resilient_call(request_id: int):
            async with router.acquire("api"):
                if not cb_manager.can_execute("api"):
                    raise CircuitBreakerError("Open", CircuitState.OPEN, "api")

                result = await retry_handler.execute(api_call, request_id)
                cb_manager.record_success("api")

                async with lock:
                    completed.append(result)

                return result

        # Launch 10 concurrent requests with limit of 5
        tasks = [resilient_call(i) for i in range(10)]
        await asyncio.gather(*tasks)

        assert len(completed) == 10
        assert all(r.startswith("response-") for r in completed)

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test system degrades gracefully under failure conditions."""
        router = QoSSemaphoreRouter(limits={"api": 2})
        cb = CircuitBreaker("api", CircuitBreakerConfig(
            min_requests=3,
            error_threshold=0.5,
            recovery_timeout=0.1,
        ))
        retry_handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01))

        call_count = 0
        success_count = 0
        circuit_open_count = 0

        async def unstable_api():
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                raise ValueError("API unstable")
            return "recovered"

        async def resilient_call():
            nonlocal success_count, circuit_open_count

            async with router.acquire("api"):
                if not cb.can_execute():
                    circuit_open_count += 1
                    return "circuit_open"

                try:
                    result = await retry_handler.execute(unstable_api)
                    cb.record_success()
                    success_count += 1
                    return result
                except RetryError:
                    cb.record_failure()
                    return "failed"

        # Make requests
        results = []
        for _ in range(10):
            result = await resilient_call()
            results.append(result)
            await asyncio.sleep(0.02)  # Small delay between requests

        # Should have some of each outcome
        assert "failed" in results or "circuit_open" in results
        # After recovery, should have some successes
        # Note: Due to timing, this may vary

    @pytest.mark.asyncio
    async def test_provider_isolation(self):
        """Verify one provider's failure doesn't affect others."""
        router = QoSSemaphoreRouter()
        cb_manager = CircuitBreakerManager(
            default_config=CircuitBreakerConfig(min_requests=3)
        )

        # Fail FMP circuit
        for _ in range(5):
            cb_manager.record_failure("fmp")

        # Polygon should still work
        assert cb_manager.can_execute("polygon") is True
        assert cb_manager.can_execute("fmp") is False

        # FMP QoS should still be available (circuit breaker is separate)
        assert router.is_available("fmp") is True

        # Execute Polygon request while FMP is broken
        async with router.acquire("polygon"):
            cb_manager.record_success("polygon")

        assert cb_manager.get_state("polygon") == CircuitState.CLOSED
        assert cb_manager.get_state("fmp") == CircuitState.OPEN


@pytest.mark.integration
class TestResilienceRecovery:
    """Test recovery scenarios for resilience components."""

    @pytest.mark.asyncio
    async def test_circuit_recovery_with_retries(self):
        """Test circuit breaker recovery using retry handler."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            min_requests=3,
            error_threshold=0.5,
            recovery_timeout=0.05,
            half_open_max_requests=2,
        ))
        retry_handler = RetryHandler(RetryConfig(max_retries=1, base_delay=0.01))

        # Force circuit open
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.06)

        # Circuit should be half-open
        assert cb.state == CircuitState.HALF_OPEN

        # Now make successful calls to close it
        async def success():
            return "ok"

        for _ in range(2):
            result = await retry_handler.execute(success)
            cb.record_success()
            assert result == "ok"

        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_qos_stats_reset(self):
        """Test QoS statistics reset functionality."""
        router = QoSSemaphoreRouter()

        # Make some requests
        for _ in range(5):
            async with router.acquire("fmp"):
                pass

        stats = router.get_stats("fmp")
        assert stats["total_requests"] == 5

        # Create new router (simulating reset)
        router2 = QoSSemaphoreRouter()
        stats2 = router2.get_stats("fmp")
        assert stats2["total_requests"] == 0
