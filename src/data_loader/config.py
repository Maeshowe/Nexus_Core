"""
OmniData Nexus Core - Configuration Manager

Centralized configuration management with environment variable loading,
validation, and sensible defaults.
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class OperatingMode(Enum):
    """Operating mode for the DataLoader."""

    LIVE = "LIVE"  # Fetch from APIs and cache
    READ_ONLY = "READ_ONLY"  # Only read from cache, no API calls


class LogLevel(Enum):
    """Logging level configuration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ProviderConfig:
    """Configuration for a specific data provider."""

    api_key: str
    base_url: str
    max_concurrency: int
    timeout: float = 30.0


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    base_dir: Path
    ttl_days: int = 7
    enabled: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration settings."""

    error_threshold: float = 0.2  # 20% error rate triggers open state
    recovery_timeout: float = 60.0  # Seconds in open state before half-open
    min_requests: int = 10  # Minimum requests before evaluating error rate


@dataclass
class RetryConfig:
    """Retry configuration settings."""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay between retries
    exponential_base: float = 2.0  # Exponential backoff multiplier


@dataclass
class Config:
    """
    Main configuration class for OmniData Nexus Core.

    Loads configuration from environment variables with sensible defaults.
    Uses python-dotenv to load from .env file if present.

    Usage:
        config = Config()  # Loads from environment
        config = Config.from_env()  # Explicit loading
        config = Config.from_dict({...})  # From dictionary

    Attributes:
        fmp: FMP provider configuration
        polygon: Polygon provider configuration
        fred: FRED provider configuration
        cache: Cache configuration
        circuit_breaker: Circuit breaker configuration
        retry: Retry configuration
        operating_mode: Current operating mode (LIVE or READ_ONLY)
        log_level: Logging level
        project_root: Project root directory
    """

    fmp: ProviderConfig
    polygon: ProviderConfig
    fred: ProviderConfig
    cache: CacheConfig
    circuit_breaker: CircuitBreakerConfig
    retry: RetryConfig
    operating_mode: OperatingMode
    log_level: LogLevel
    project_root: Path

    # Provider base URLs
    FMP_BASE_URL: str = "https://financialmodelingprep.com"  # Updated to new stable API (Aug 2025)
    POLYGON_BASE_URL: str = "https://api.polygon.io"
    FRED_BASE_URL: str = "https://api.stlouisfed.org/fred"

    # Provider concurrency limits (QoS)
    FMP_MAX_CONCURRENCY: int = 3
    POLYGON_MAX_CONCURRENCY: int = 10
    FRED_MAX_CONCURRENCY: int = 1

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If None, searches for .env
                     in project root and parent directories.

        Returns:
            Configured Config instance.

        Raises:
            ValueError: If required API keys are missing.
        """
        # Determine project root (directory containing src/)
        project_root = cls._find_project_root()

        # Load .env file
        if env_path:
            load_dotenv(env_path)
        else:
            # Try project root first, then current directory
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            else:
                load_dotenv()  # Try default locations

        # Get API keys
        fmp_key = os.getenv("FMP_KEY", "")
        polygon_key = os.getenv("POLYGON_KEY", "")
        fred_key = os.getenv("FRED_KEY", "")

        # Get optional settings with defaults
        cache_ttl_days = int(os.getenv("CACHE_TTL_DAYS", "7"))
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        cb_threshold = float(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "0.2"))
        cb_timeout = float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
        request_timeout = float(os.getenv("REQUEST_TIMEOUT", "30"))
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        operating_mode_str = os.getenv("OPERATING_MODE", "LIVE").upper()

        # Parse enums
        try:
            log_level = LogLevel[log_level_str]
        except KeyError:
            log_level = LogLevel.INFO

        try:
            operating_mode = OperatingMode[operating_mode_str]
        except KeyError:
            operating_mode = OperatingMode.LIVE

        # Build provider configs
        fmp_config = ProviderConfig(
            api_key=fmp_key,
            base_url=cls.FMP_BASE_URL,
            max_concurrency=cls.FMP_MAX_CONCURRENCY,
            timeout=request_timeout,
        )

        polygon_config = ProviderConfig(
            api_key=polygon_key,
            base_url=cls.POLYGON_BASE_URL,
            max_concurrency=cls.POLYGON_MAX_CONCURRENCY,
            timeout=request_timeout,
        )

        fred_config = ProviderConfig(
            api_key=fred_key,
            base_url=cls.FRED_BASE_URL,
            max_concurrency=cls.FRED_MAX_CONCURRENCY,
            timeout=request_timeout,
        )

        # Build cache config
        cache_dir = project_root / "data" / "cache"
        cache_config = CacheConfig(
            base_dir=cache_dir,
            ttl_days=cache_ttl_days,
            enabled=True,
        )

        # Build circuit breaker config
        cb_config = CircuitBreakerConfig(
            error_threshold=cb_threshold,
            recovery_timeout=cb_timeout,
        )

        # Build retry config
        retry_config = RetryConfig(
            max_retries=max_retries,
        )

        return cls(
            fmp=fmp_config,
            polygon=polygon_config,
            fred=fred_config,
            cache=cache_config,
            circuit_breaker=cb_config,
            retry=retry_config,
            operating_mode=operating_mode,
            log_level=log_level,
            project_root=project_root,
        )

    @staticmethod
    def _find_project_root() -> Path:
        """
        Find the project root directory.

        Looks for a directory containing 'src' folder, walking up from
        the current file's location.

        Returns:
            Path to project root directory.
        """
        # Start from this file's directory
        current = Path(__file__).resolve().parent

        # Walk up until we find a directory with 'src' as a child
        for _ in range(10):  # Limit search depth
            if (current / "src").is_dir():
                return current
            if (current.parent / "src").is_dir():
                return current.parent
            parent = current.parent
            if parent == current:
                break  # Reached filesystem root
            current = parent

        # Fallback to current working directory
        return Path.cwd()

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []

        # Check API keys in LIVE mode
        if self.operating_mode == OperatingMode.LIVE:
            if not self.fmp.api_key:
                errors.append("FMP_KEY is required in LIVE mode")
            if not self.polygon.api_key:
                errors.append("POLYGON_KEY is required in LIVE mode")
            if not self.fred.api_key:
                errors.append("FRED_KEY is required in LIVE mode")

        # Validate numeric ranges
        if self.cache.ttl_days < 1:
            errors.append("CACHE_TTL_DAYS must be at least 1")
        if self.retry.max_retries < 0:
            errors.append("MAX_RETRIES must be non-negative")
        if not (0 < self.circuit_breaker.error_threshold <= 1):
            errors.append("CIRCUIT_BREAKER_THRESHOLD must be between 0 and 1")
        if self.circuit_breaker.recovery_timeout < 1:
            errors.append("CIRCUIT_BREAKER_TIMEOUT must be at least 1 second")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_cache_dir(self, provider: str) -> Path:
        """
        Get the cache directory for a specific provider.

        Args:
            provider: Provider name ('fmp', 'polygon', or 'fred')

        Returns:
            Path to provider-specific cache directory.
        """
        return self.cache.base_dir / f"{provider}_cache"

    def get_log_dir(self) -> Path:
        """Get the logs directory."""
        return self.project_root / "logs"

    def has_api_key(self, provider: str) -> bool:
        """
        Check if an API key is configured for a provider.

        Args:
            provider: Provider name ('fmp', 'polygon', or 'fred')

        Returns:
            True if API key is set and non-empty.
        """
        provider_config = getattr(self, provider, None)
        if provider_config and hasattr(provider_config, "api_key"):
            return bool(provider_config.api_key)
        return False

    def __post_init__(self):
        """Ensure cache directory exists after initialization."""
        self.cache.base_dir.mkdir(parents=True, exist_ok=True)


# Convenience function for simple usage
def load_config(env_path: Optional[Path] = None) -> Config:
    """
    Load configuration from environment.

    This is a convenience function that creates a Config instance
    by loading from environment variables.

    Args:
        env_path: Optional path to .env file.

    Returns:
        Configured Config instance.
    """
    return Config.from_env(env_path)
