"""
Unit tests for the health monitor.
"""

import time

import pytest

from data_loader.health import (
    HealthMonitor,
    ProviderMetrics,
    ProviderStatus,
    RequestMetrics,
)


@pytest.mark.unit
class TestProviderStatus:
    """Tests for ProviderStatus enum."""

    def test_all_statuses(self):
        assert ProviderStatus.HEALTHY.value == "healthy"
        assert ProviderStatus.DEGRADED.value == "degraded"
        assert ProviderStatus.UNHEALTHY.value == "unhealthy"
        assert ProviderStatus.UNKNOWN.value == "unknown"


@pytest.mark.unit
class TestRequestMetrics:
    """Tests for RequestMetrics dataclass."""

    def test_create_metrics(self):
        metrics = RequestMetrics(
            provider="fmp",
            endpoint="profile",
            success=True,
            status_code=200,
            latency_ms=150.5,
            timestamp=time.time(),
        )
        assert metrics.provider == "fmp"
        assert metrics.endpoint == "profile"
        assert metrics.success is True
        assert metrics.status_code == 200
        assert metrics.latency_ms == 150.5

    def test_failed_metrics(self):
        metrics = RequestMetrics(
            provider="fmp",
            endpoint="profile",
            success=False,
            status_code=500,
            latency_ms=50.0,
            timestamp=time.time(),
            error_type="server_error",
        )
        assert metrics.success is False
        assert metrics.error_type == "server_error"


@pytest.mark.unit
class TestProviderMetrics:
    """Tests for ProviderMetrics dataclass."""

    def test_default_values(self):
        metrics = ProviderMetrics(provider="fmp")
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.error_rate == 0.0
        assert metrics.status == ProviderStatus.UNKNOWN

    def test_to_dict(self):
        metrics = ProviderMetrics(
            provider="fmp",
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            rate_limited_requests=2,
            timeout_requests=3,
            avg_latency_ms=125.5678,
            min_latency_ms=50.0,
            max_latency_ms=500.0,
            error_rate=0.1,
            status=ProviderStatus.DEGRADED,
        )
        d = metrics.to_dict()

        assert d["provider"] == "fmp"
        assert d["status"] == "degraded"
        assert d["total_requests"] == 100
        assert d["error_rate"] == 0.1
        assert d["avg_latency_ms"] == 125.57  # Rounded


@pytest.mark.unit
class TestHealthMonitor:
    """Tests for HealthMonitor class."""

    def test_init_default(self):
        monitor = HealthMonitor()
        assert monitor.window_size == 100

    def test_init_custom_window(self):
        monitor = HealthMonitor(window_size=50)
        assert monitor.window_size == 50

    def test_record_success(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0

    def test_record_failure(self):
        monitor = HealthMonitor()

        monitor.record_failure(
            "fmp", "profile",
            latency_ms=50.0,
            status_code=500,
            error_type="server_error"
        )

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1

    def test_record_rate_limit(self):
        monitor = HealthMonitor()

        monitor.record_failure(
            "fmp", "profile",
            latency_ms=10.0,
            status_code=429,
            error_type="rate_limit"
        )

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.rate_limited_requests == 1

    def test_record_timeout(self):
        monitor = HealthMonitor()

        monitor.record_failure(
            "fmp", "profile",
            latency_ms=30000.0,
            error_type="timeout"
        )

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.timeout_requests == 1

    def test_error_rate_calculation(self):
        monitor = HealthMonitor()

        # 8 successes, 2 failures = 20% error rate
        for _ in range(8):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(2):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.error_rate == 0.2

    def test_latency_stats(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)
        monitor.record_success("fmp", "profile", latency_ms=200.0)
        monitor.record_success("fmp", "profile", latency_ms=300.0)

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.avg_latency_ms == 200.0
        assert metrics.min_latency_ms == 100.0
        assert metrics.max_latency_ms == 300.0

    def test_status_unknown_few_requests(self):
        monitor = HealthMonitor()

        # Less than MIN_REQUESTS_FOR_STATUS
        for _ in range(5):
            monitor.record_success("fmp", "profile", latency_ms=100.0)

        status = monitor.get_provider_status("fmp")
        assert status == ProviderStatus.UNKNOWN

    def test_status_healthy(self):
        monitor = HealthMonitor()

        # 15 requests with 0% error rate
        for _ in range(15):
            monitor.record_success("fmp", "profile", latency_ms=100.0)

        status = monitor.get_provider_status("fmp")
        assert status == ProviderStatus.HEALTHY

    def test_status_degraded(self):
        monitor = HealthMonitor()

        # 15% error rate (between 10% and 20%)
        for _ in range(85):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(15):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        status = monitor.get_provider_status("fmp")
        assert status == ProviderStatus.DEGRADED

    def test_status_unhealthy(self):
        monitor = HealthMonitor()

        # 25% error rate (above 20%)
        for _ in range(75):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(25):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        status = monitor.get_provider_status("fmp")
        assert status == ProviderStatus.UNHEALTHY

    def test_is_healthy(self):
        monitor = HealthMonitor()

        # Unknown is considered healthy (not enough data)
        assert monitor.is_healthy("fmp") is True

        # After enough successful requests
        for _ in range(15):
            monitor.record_success("fmp", "profile", latency_ms=100.0)

        assert monitor.is_healthy("fmp") is True

    def test_is_not_healthy(self):
        monitor = HealthMonitor()

        # 30% error rate
        for _ in range(70):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(30):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        assert monitor.is_healthy("fmp") is False

    def test_get_health_report(self):
        monitor = HealthMonitor()

        # Add some requests
        for _ in range(20):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(15):
            monitor.record_success("polygon", "aggs", latency_ms=150.0)

        report = monitor.get_health_report()

        assert "timestamp" in report
        assert "providers" in report
        assert "overall_status" in report
        assert "fmp" in report["providers"]
        assert "polygon" in report["providers"]
        assert "fred" in report["providers"]

    def test_overall_status_healthy(self):
        monitor = HealthMonitor()

        # All providers healthy
        for _ in range(15):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
            monitor.record_success("polygon", "aggs", latency_ms=100.0)
            monitor.record_success("fred", "series", latency_ms=100.0)

        report = monitor.get_health_report()
        assert report["overall_status"] == "healthy"

    def test_overall_status_degraded(self):
        monitor = HealthMonitor()

        # FMP healthy, Polygon degraded (15% error)
        for _ in range(15):
            monitor.record_success("fmp", "profile", latency_ms=100.0)

        for _ in range(85):
            monitor.record_success("polygon", "aggs", latency_ms=100.0)
        for _ in range(15):
            monitor.record_failure("polygon", "aggs", latency_ms=50.0)

        report = monitor.get_health_report()
        assert report["overall_status"] == "degraded"

    def test_overall_status_unhealthy(self):
        monitor = HealthMonitor()

        # One provider unhealthy
        for _ in range(75):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        for _ in range(25):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        report = monitor.get_health_report()
        assert report["overall_status"] == "unhealthy"

    def test_reset_single_provider(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)
        monitor.record_success("polygon", "aggs", latency_ms=100.0)

        monitor.reset("fmp")

        fmp_metrics = monitor.get_provider_metrics("fmp")
        polygon_metrics = monitor.get_provider_metrics("polygon")

        assert fmp_metrics.total_requests == 0
        assert polygon_metrics.total_requests == 1

    def test_reset_all_providers(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)
        monitor.record_success("polygon", "aggs", latency_ms=100.0)
        monitor.record_success("fred", "series", latency_ms=100.0)

        monitor.reset()

        for provider in ["fmp", "polygon", "fred"]:
            metrics = monitor.get_provider_metrics(provider)
            assert metrics.total_requests == 0

    def test_get_error_rate(self):
        monitor = HealthMonitor()

        for _ in range(9):
            monitor.record_success("fmp", "profile", latency_ms=100.0)
        monitor.record_failure("fmp", "profile", latency_ms=50.0)

        error_rate = monitor.get_error_rate("fmp")
        assert error_rate == 0.1

    def test_get_avg_latency(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)
        monitor.record_success("fmp", "profile", latency_ms=200.0)

        avg_latency = monitor.get_avg_latency("fmp")
        assert avg_latency == 150.0

    def test_rolling_window(self):
        monitor = HealthMonitor(window_size=10)

        # Record 10 successes
        for _ in range(10):
            monitor.record_success("fmp", "profile", latency_ms=100.0)

        # Error rate should be 0
        assert monitor.get_error_rate("fmp") == 0.0

        # Now record 5 failures - only last 10 in window
        for _ in range(5):
            monitor.record_failure("fmp", "profile", latency_ms=50.0)

        # Window now has 5 successes and 5 failures = 50% error rate
        assert monitor.get_error_rate("fmp") == 0.5

    def test_new_provider(self):
        monitor = HealthMonitor()

        # Record for a new provider (not in default list)
        monitor.record_success("custom", "endpoint", latency_ms=100.0)

        metrics = monitor.get_provider_metrics("custom")
        assert metrics.total_requests == 1

    def test_last_success_and_error_tracking(self):
        monitor = HealthMonitor()

        monitor.record_success("fmp", "profile", latency_ms=100.0)
        time.sleep(0.01)  # Small delay
        monitor.record_failure("fmp", "profile", latency_ms=50.0, error_type="server_error")

        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.last_success is not None
        assert metrics.last_error is not None
        assert metrics.last_error_type == "server_error"
        assert metrics.last_error > metrics.last_success

    def test_thread_safety(self):
        import threading

        monitor = HealthMonitor()
        errors = []

        def record_many():
            try:
                for _ in range(100):
                    monitor.record_success("fmp", "profile", latency_ms=100.0)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_many) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        metrics = monitor.get_provider_metrics("fmp")
        assert metrics.total_requests == 1000
