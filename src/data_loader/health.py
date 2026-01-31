"""
OmniData Nexus Core - Health Monitor

Tracks API status, metrics, and provides health reports for all providers.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Optional


class ProviderStatus(Enum):
    """Health status for a provider."""

    HEALTHY = "healthy"  # Normal operation
    DEGRADED = "degraded"  # Elevated errors but still functional
    UNHEALTHY = "unhealthy"  # Circuit breaker open or critical failure
    UNKNOWN = "unknown"  # Not enough data


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    provider: str
    endpoint: str
    success: bool
    status_code: Optional[int]
    latency_ms: float
    timestamp: float
    error_type: Optional[str] = None


@dataclass
class ProviderMetrics:
    """Aggregated metrics for a provider."""

    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    timeout_requests: int = 0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    error_rate: float = 0.0
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_success: Optional[float] = None
    last_error: Optional[float] = None
    last_error_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "provider": self.provider,
            "status": self.status.value,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "timeout_requests": self.timeout_requests,
            "error_rate": round(self.error_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "min_latency_ms": round(self.min_latency_ms, 2) if self.min_latency_ms != float('inf') else 0,
            "max_latency_ms": round(self.max_latency_ms, 2),
            "last_success": self.last_success,
            "last_error": self.last_error,
            "last_error_type": self.last_error_type,
        }


class HealthMonitor:
    """
    Tracks health and metrics for all data providers.

    Features:
    - Per-provider request tracking
    - Rolling window for recent metrics
    - Error rate calculation
    - Health status determination
    - Thread-safe operations

    Usage:
        monitor = HealthMonitor()

        # Record a successful request
        monitor.record_request(
            provider="fmp",
            endpoint="profile",
            success=True,
            status_code=200,
            latency_ms=150.5
        )

        # Get health report
        report = monitor.get_health_report()
        print(report["fmp"]["status"])  # "healthy"
    """

    # Thresholds for status determination
    ERROR_RATE_DEGRADED = 0.1  # 10% errors = degraded
    ERROR_RATE_UNHEALTHY = 0.2  # 20% errors = unhealthy
    MIN_REQUESTS_FOR_STATUS = 10  # Minimum requests before evaluating

    def __init__(self, window_size: int = 100):
        """
        Initialize health monitor.

        Args:
            window_size: Number of recent requests to track per provider
        """
        self.window_size = window_size
        self._lock = Lock()

        # Per-provider request history (rolling window)
        self._history: dict[str, deque[RequestMetrics]] = {
            "fmp": deque(maxlen=window_size),
            "polygon": deque(maxlen=window_size),
            "fred": deque(maxlen=window_size),
        }

        # Cumulative counters (total since startup)
        self._total_counters: dict[str, dict] = {
            provider: {
                "total": 0,
                "success": 0,
                "failed": 0,
                "rate_limited": 0,
                "timeout": 0,
            }
            for provider in ["fmp", "polygon", "fred"]
        }

    def record_request(
        self,
        provider: str,
        endpoint: str,
        success: bool,
        status_code: Optional[int],
        latency_ms: float,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Record a request for metrics tracking.

        Args:
            provider: Provider name (fmp, polygon, fred)
            endpoint: API endpoint called
            success: Whether request succeeded
            status_code: HTTP status code (if any)
            latency_ms: Request latency in milliseconds
            error_type: Type of error (if failed)
        """
        metrics = RequestMetrics(
            provider=provider,
            endpoint=endpoint,
            success=success,
            status_code=status_code,
            latency_ms=latency_ms,
            timestamp=time.time(),
            error_type=error_type,
        )

        with self._lock:
            if provider not in self._history:
                self._history[provider] = deque(maxlen=self.window_size)
                self._total_counters[provider] = {
                    "total": 0, "success": 0, "failed": 0,
                    "rate_limited": 0, "timeout": 0,
                }

            self._history[provider].append(metrics)

            # Update cumulative counters
            counters = self._total_counters[provider]
            counters["total"] += 1

            if success:
                counters["success"] += 1
            else:
                counters["failed"] += 1
                if status_code == 429:
                    counters["rate_limited"] += 1
                if error_type == "timeout":
                    counters["timeout"] += 1

    def get_provider_metrics(self, provider: str) -> ProviderMetrics:
        """
        Get aggregated metrics for a provider.

        Args:
            provider: Provider name

        Returns:
            ProviderMetrics with current statistics
        """
        with self._lock:
            history = self._history.get(provider, deque())
            counters = self._total_counters.get(provider, {
                "total": 0, "success": 0, "failed": 0,
                "rate_limited": 0, "timeout": 0,
            })

            metrics = ProviderMetrics(provider=provider)

            # Use cumulative counters for totals
            metrics.total_requests = counters["total"]
            metrics.successful_requests = counters["success"]
            metrics.failed_requests = counters["failed"]
            metrics.rate_limited_requests = counters["rate_limited"]
            metrics.timeout_requests = counters["timeout"]

            # Calculate error rate from recent history (rolling window)
            if history:
                recent_failures = sum(1 for m in history if not m.success)
                metrics.error_rate = recent_failures / len(history)

                # Calculate latency stats from history
                latencies = [m.latency_ms for m in history]
                metrics.avg_latency_ms = sum(latencies) / len(latencies)
                metrics.min_latency_ms = min(latencies)
                metrics.max_latency_ms = max(latencies)

                # Find last success/error
                for m in reversed(history):
                    if m.success and metrics.last_success is None:
                        metrics.last_success = m.timestamp
                    if not m.success and metrics.last_error is None:
                        metrics.last_error = m.timestamp
                        metrics.last_error_type = m.error_type
                    if metrics.last_success and metrics.last_error:
                        break

            # Determine status
            metrics.status = self._determine_status(metrics)

            return metrics

    def _determine_status(self, metrics: ProviderMetrics) -> ProviderStatus:
        """Determine health status based on metrics."""
        if metrics.total_requests < self.MIN_REQUESTS_FOR_STATUS:
            return ProviderStatus.UNKNOWN

        if metrics.error_rate >= self.ERROR_RATE_UNHEALTHY:
            return ProviderStatus.UNHEALTHY

        if metrics.error_rate >= self.ERROR_RATE_DEGRADED:
            return ProviderStatus.DEGRADED

        return ProviderStatus.HEALTHY

    def get_health_report(self) -> dict:
        """
        Get health report for all providers.

        Returns:
            Dictionary with metrics for each provider and overall status
        """
        report = {
            "timestamp": time.time(),
            "providers": {},
            "overall_status": ProviderStatus.HEALTHY.value,
        }

        statuses = []
        for provider in ["fmp", "polygon", "fred"]:
            metrics = self.get_provider_metrics(provider)
            report["providers"][provider] = metrics.to_dict()
            statuses.append(metrics.status)

        # Overall status is the worst of all providers
        if ProviderStatus.UNHEALTHY in statuses:
            report["overall_status"] = ProviderStatus.UNHEALTHY.value
        elif ProviderStatus.DEGRADED in statuses:
            report["overall_status"] = ProviderStatus.DEGRADED.value
        elif all(s == ProviderStatus.UNKNOWN for s in statuses):
            report["overall_status"] = ProviderStatus.UNKNOWN.value

        return report

    def get_provider_status(self, provider: str) -> ProviderStatus:
        """
        Get current health status for a provider.

        Args:
            provider: Provider name

        Returns:
            ProviderStatus enum value
        """
        metrics = self.get_provider_metrics(provider)
        return metrics.status

    def is_healthy(self, provider: str) -> bool:
        """
        Check if a provider is healthy.

        Args:
            provider: Provider name

        Returns:
            True if provider is healthy or unknown (not enough data)
        """
        status = self.get_provider_status(provider)
        return status in (ProviderStatus.HEALTHY, ProviderStatus.UNKNOWN)

    def get_error_rate(self, provider: str) -> float:
        """
        Get current error rate for a provider.

        Args:
            provider: Provider name

        Returns:
            Error rate as a float (0.0 to 1.0)
        """
        metrics = self.get_provider_metrics(provider)
        return metrics.error_rate

    def get_avg_latency(self, provider: str) -> float:
        """
        Get average latency for a provider.

        Args:
            provider: Provider name

        Returns:
            Average latency in milliseconds
        """
        metrics = self.get_provider_metrics(provider)
        return metrics.avg_latency_ms

    def reset(self, provider: Optional[str] = None) -> None:
        """
        Reset metrics for a provider or all providers.

        Args:
            provider: Optional provider to reset, or None for all
        """
        with self._lock:
            providers = [provider] if provider else ["fmp", "polygon", "fred"]

            for p in providers:
                if p in self._history:
                    self._history[p].clear()
                if p in self._total_counters:
                    self._total_counters[p] = {
                        "total": 0, "success": 0, "failed": 0,
                        "rate_limited": 0, "timeout": 0,
                    }

    def record_success(
        self,
        provider: str,
        endpoint: str,
        latency_ms: float,
        status_code: int = 200,
    ) -> None:
        """
        Convenience method to record a successful request.

        Args:
            provider: Provider name
            endpoint: API endpoint
            latency_ms: Request latency
            status_code: HTTP status code
        """
        self.record_request(
            provider=provider,
            endpoint=endpoint,
            success=True,
            status_code=status_code,
            latency_ms=latency_ms,
        )

    def record_failure(
        self,
        provider: str,
        endpoint: str,
        latency_ms: float,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Convenience method to record a failed request.

        Args:
            provider: Provider name
            endpoint: API endpoint
            latency_ms: Request latency
            status_code: HTTP status code (if any)
            error_type: Type of error
        """
        self.record_request(
            provider=provider,
            endpoint=endpoint,
            success=False,
            status_code=status_code,
            latency_ms=latency_ms,
            error_type=error_type,
        )
