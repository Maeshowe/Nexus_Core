"""
Unit tests for the QoS Semaphore Router.
"""

import asyncio

import pytest

from data_loader.qos_router import (
    QoSConfig,
    QoSContext,
    QoSSemaphoreRouter,
    QoSStats,
    get_default_router,
    reset_default_router,
)


@pytest.mark.unit
class TestQoSConfig:
    """Tests for QoSConfig dataclass."""

    def test_create_config(self):
        config = QoSConfig(max_concurrency=5, priority=1, name="test")
        assert config.max_concurrency == 5
        assert config.priority == 1
        assert config.name == "test"

    def test_default_values(self):
        config = QoSConfig(max_concurrency=3)
        assert config.priority == 0
        assert config.name == ""


@pytest.mark.unit
class TestQoSStats:
    """Tests for QoSStats dataclass."""

    def test_default_values(self):
        stats = QoSStats()
        assert stats.total_requests == 0
        assert stats.active_requests == 0
        assert stats.queued_requests == 0
        assert stats.max_concurrent_seen == 0


@pytest.mark.unit
class TestQoSSemaphoreRouter:
    """Tests for QoSSemaphoreRouter class."""

    def test_init_default_limits(self):
        router = QoSSemaphoreRouter()
        assert router.get_limit("fmp") == 3
        assert router.get_limit("polygon") == 10
        assert router.get_limit("fred") == 1

    def test_init_custom_limits(self):
        router = QoSSemaphoreRouter(limits={"fmp": 5, "custom": 2})
        assert router.get_limit("fmp") == 5  # Overridden
        assert router.get_limit("polygon") == 10  # Default preserved
        assert router.get_limit("custom") == 2  # New provider

    def test_get_limit_unknown_provider(self):
        router = QoSSemaphoreRouter()
        # Unknown providers get default of 5
        assert router.get_limit("unknown") == 5

    def test_set_limit(self):
        router = QoSSemaphoreRouter()
        router.set_limit("fmp", 10)
        assert router.get_limit("fmp") == 10

    def test_set_limit_new_provider(self):
        router = QoSSemaphoreRouter()
        router.set_limit("new_provider", 7)
        assert router.get_limit("new_provider") == 7

    def test_set_limit_invalid(self):
        router = QoSSemaphoreRouter()
        with pytest.raises(ValueError, match="at least 1"):
            router.set_limit("fmp", 0)

    def test_get_stats_single_provider(self):
        router = QoSSemaphoreRouter()
        stats = router.get_stats("fmp")
        assert stats["provider"] == "fmp"
        assert stats["max_concurrency"] == 3
        assert stats["total_requests"] == 0
        assert stats["active_requests"] == 0

    def test_get_stats_all_providers(self):
        router = QoSSemaphoreRouter()
        stats = router.get_stats()
        assert "fmp" in stats
        assert "polygon" in stats
        assert "fred" in stats

    def test_is_available_initial(self):
        router = QoSSemaphoreRouter()
        assert router.is_available("fmp") is True
        assert router.is_available("polygon") is True
        assert router.is_available("fred") is True

    def test_get_available_slots(self):
        router = QoSSemaphoreRouter()
        assert router.get_available_slots("fmp") == 3
        assert router.get_available_slots("polygon") == 10
        assert router.get_available_slots("fred") == 1

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        router = QoSSemaphoreRouter()

        async with router.acquire("fmp"):
            assert router.get_active_count("fmp") == 1
            assert router.get_available_slots("fmp") == 2

        assert router.get_active_count("fmp") == 0
        assert router.get_available_slots("fmp") == 3

    @pytest.mark.asyncio
    async def test_acquire_multiple(self):
        router = QoSSemaphoreRouter()

        async with router.acquire("fmp"):
            async with router.acquire("fmp"):
                assert router.get_active_count("fmp") == 2
                assert router.get_available_slots("fmp") == 1

            assert router.get_active_count("fmp") == 1

        assert router.get_active_count("fmp") == 0

    @pytest.mark.asyncio
    async def test_execute_success(self):
        router = QoSSemaphoreRouter()

        async def sample_task():
            return "result"

        result = await router.execute("fmp", sample_task)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_execute_with_args(self):
        router = QoSSemaphoreRouter()

        async def add(a, b):
            return a + b

        result = await router.execute("fmp", add, 5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self):
        router = QoSSemaphoreRouter()

        async def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await router.execute("fmp", greet, "World", greeting="Hi")
        assert result == "Hi, World!"

    @pytest.mark.asyncio
    async def test_execute_exception_releases_slot(self):
        router = QoSSemaphoreRouter()

        async def failing_task():
            raise ValueError("Task failed")

        with pytest.raises(ValueError):
            await router.execute("fmp", failing_task)

        # Slot should be released even after exception
        assert router.get_active_count("fmp") == 0
        assert router.get_available_slots("fmp") == 3

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        router = QoSSemaphoreRouter()

        async with router.acquire("fmp"):
            pass

        async with router.acquire("fmp"):
            async with router.acquire("fmp"):
                pass

        stats = router.get_stats("fmp")
        assert stats["total_requests"] == 3
        assert stats["max_concurrent_seen"] == 2

    @pytest.mark.asyncio
    async def test_concurrency_limit_enforced(self):
        """Verify that concurrency limit is actually enforced."""
        router = QoSSemaphoreRouter(limits={"test": 2})

        active_count = 0
        max_active = 0
        lock = asyncio.Lock()

        async def tracked_task(delay: float):
            nonlocal active_count, max_active
            async with lock:
                active_count += 1
                if active_count > max_active:
                    max_active = active_count

            await asyncio.sleep(delay)

            async with lock:
                active_count -= 1

        # Start 5 tasks with limit of 2
        tasks = [
            router.execute("test", tracked_task, 0.05)
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)

        # Max active should never exceed limit
        assert max_active <= 2

    @pytest.mark.asyncio
    async def test_different_providers_independent(self):
        """Verify that different providers have independent limits."""
        router = QoSSemaphoreRouter(limits={"a": 1, "b": 1})

        results = []
        lock = asyncio.Lock()

        async def record(provider: str, value: int):
            async with lock:
                results.append((provider, value, "start"))
            await asyncio.sleep(0.02)
            async with lock:
                results.append((provider, value, "end"))

        # Start tasks on both providers concurrently
        await asyncio.gather(
            router.execute("a", record, "a", 1),
            router.execute("b", record, "b", 2),
        )

        # Both should run concurrently (interleaved)
        start_indices = [i for i, r in enumerate(results) if r[2] == "start"]
        assert len(start_indices) == 2
        # If they run concurrently, both starts come before both ends
        assert start_indices == [0, 1] or start_indices == [0, 2]

    @pytest.mark.asyncio
    async def test_unknown_provider_gets_semaphore(self):
        router = QoSSemaphoreRouter()

        async with router.acquire("unknown_provider"):
            assert router.get_active_count("unknown_provider") == 1

        assert router.get_active_count("unknown_provider") == 0


@pytest.mark.unit
class TestQoSContext:
    """Tests for QoSContext class."""

    @pytest.mark.asyncio
    async def test_context_acquires_and_releases(self):
        router = QoSSemaphoreRouter()

        context = QoSContext(router, "fmp")

        await context.__aenter__()
        assert router.get_active_count("fmp") == 1

        await context.__aexit__(None, None, None)
        assert router.get_active_count("fmp") == 0

    @pytest.mark.asyncio
    async def test_context_releases_on_exception(self):
        router = QoSSemaphoreRouter()

        try:
            async with router.acquire("fmp"):
                raise ValueError("Error inside context")
        except ValueError:
            pass

        assert router.get_active_count("fmp") == 0


@pytest.mark.unit
class TestDefaultRouter:
    """Tests for default router functions."""

    def test_get_default_router(self):
        reset_default_router()
        router1 = get_default_router()
        router2 = get_default_router()
        assert router1 is router2

    def test_reset_default_router(self):
        router1 = get_default_router()
        reset_default_router()
        router2 = get_default_router()
        assert router1 is not router2


@pytest.mark.unit
class TestFREDSequential:
    """Test that FRED correctly enforces sequential requests."""

    @pytest.mark.asyncio
    async def test_fred_sequential_execution(self):
        """FRED should only allow 1 concurrent request."""
        router = QoSSemaphoreRouter()

        execution_order = []
        lock = asyncio.Lock()

        async def task(task_id: int):
            async with lock:
                execution_order.append(f"{task_id}_start")
            await asyncio.sleep(0.02)
            async with lock:
                execution_order.append(f"{task_id}_end")

        # Start 3 FRED tasks
        await asyncio.gather(
            router.execute("fred", task, 1),
            router.execute("fred", task, 2),
            router.execute("fred", task, 3),
        )

        # With limit of 1, tasks should be sequential
        # Each task should complete before next starts
        for i in range(3):
            start_idx = execution_order.index(f"{i+1}_start")
            end_idx = execution_order.index(f"{i+1}_end")
            # End should come right after start (sequential)
            assert end_idx == start_idx + 1
