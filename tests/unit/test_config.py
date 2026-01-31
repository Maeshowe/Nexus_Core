"""
Unit tests for the configuration manager.
"""

import os
import tempfile
from pathlib import Path

import pytest

from data_loader.config import (
    CacheConfig,
    CircuitBreakerConfig,
    Config,
    LogLevel,
    OperatingMode,
    ProviderConfig,
    RetryConfig,
    load_config,
)


@pytest.mark.unit
class TestOperatingMode:
    """Tests for OperatingMode enum."""

    def test_live_mode(self):
        assert OperatingMode.LIVE.value == "LIVE"

    def test_read_only_mode(self):
        assert OperatingMode.READ_ONLY.value == "READ_ONLY"


@pytest.mark.unit
class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_all_log_levels(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"


@pytest.mark.unit
class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_create_provider_config(self):
        config = ProviderConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            max_concurrency=5,
            timeout=30.0,
        )
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.max_concurrency == 5
        assert config.timeout == 30.0

    def test_default_timeout(self):
        config = ProviderConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            max_concurrency=5,
        )
        assert config.timeout == 30.0


@pytest.mark.unit
class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_create_cache_config(self):
        config = CacheConfig(
            base_dir=Path("/tmp/cache"),
            ttl_days=14,
            enabled=True,
        )
        assert config.base_dir == Path("/tmp/cache")
        assert config.ttl_days == 14
        assert config.enabled is True

    def test_default_values(self):
        config = CacheConfig(base_dir=Path("/tmp/cache"))
        assert config.ttl_days == 7
        assert config.enabled is True


@pytest.mark.unit
class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_create_circuit_breaker_config(self):
        config = CircuitBreakerConfig(
            error_threshold=0.3,
            recovery_timeout=120.0,
            min_requests=20,
        )
        assert config.error_threshold == 0.3
        assert config.recovery_timeout == 120.0
        assert config.min_requests == 20

    def test_default_values(self):
        config = CircuitBreakerConfig()
        assert config.error_threshold == 0.2
        assert config.recovery_timeout == 60.0
        assert config.min_requests == 10


@pytest.mark.unit
class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_create_retry_config(self):
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
        )
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0

    def test_default_values(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0


@pytest.mark.unit
class TestConfig:
    """Tests for the main Config class."""

    @pytest.fixture
    def clean_env(self):
        """Remove test-related environment variables and prevent .env loading.

        This fixture temporarily renames the .env file to prevent load_dotenv()
        from reloading API keys during tests that expect default/empty values.
        """
        keys_to_remove = [
            "FMP_KEY", "POLYGON_KEY", "FRED_KEY",
            "CACHE_TTL_DAYS", "MAX_RETRIES",
            "CIRCUIT_BREAKER_THRESHOLD", "CIRCUIT_BREAKER_TIMEOUT",
            "REQUEST_TIMEOUT", "LOG_LEVEL", "OPERATING_MODE",
        ]
        original = {k: os.environ.get(k) for k in keys_to_remove}

        # Temporarily rename .env file to prevent load_dotenv() from loading it
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_backup = env_file.with_suffix(".env.bak")
        env_existed = env_file.exists()
        if env_existed:
            env_file.rename(env_backup)

        for k in keys_to_remove:
            os.environ.pop(k, None)

        yield

        # Restore .env file
        if env_existed and env_backup.exists():
            env_backup.rename(env_file)

        for k, v in original.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_from_env_with_all_keys(self, clean_env):
        """Test loading config with all environment variables set."""
        os.environ["FMP_KEY"] = "fmp_test_key"
        os.environ["POLYGON_KEY"] = "polygon_test_key"
        os.environ["FRED_KEY"] = "fred_test_key"
        os.environ["CACHE_TTL_DAYS"] = "14"
        os.environ["MAX_RETRIES"] = "5"
        os.environ["CIRCUIT_BREAKER_THRESHOLD"] = "0.3"
        os.environ["CIRCUIT_BREAKER_TIMEOUT"] = "120"
        os.environ["REQUEST_TIMEOUT"] = "45"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["OPERATING_MODE"] = "READ_ONLY"

        config = Config.from_env()

        assert config.fmp.api_key == "fmp_test_key"
        assert config.polygon.api_key == "polygon_test_key"
        assert config.fred.api_key == "fred_test_key"
        assert config.cache.ttl_days == 14
        assert config.retry.max_retries == 5
        assert config.circuit_breaker.error_threshold == 0.3
        assert config.circuit_breaker.recovery_timeout == 120.0
        assert config.fmp.timeout == 45.0
        assert config.log_level == LogLevel.DEBUG
        assert config.operating_mode == OperatingMode.READ_ONLY

    def test_from_env_with_defaults(self, clean_env):
        """Test loading config with default values."""
        config = Config.from_env()

        assert config.fmp.api_key == ""
        assert config.polygon.api_key == ""
        assert config.fred.api_key == ""
        assert config.cache.ttl_days == 7
        assert config.retry.max_retries == 3
        assert config.circuit_breaker.error_threshold == 0.2
        assert config.circuit_breaker.recovery_timeout == 60.0
        assert config.log_level == LogLevel.INFO
        assert config.operating_mode == OperatingMode.LIVE

    def test_from_env_with_env_file(self, clean_env):
        """Test loading config from a .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("FMP_KEY=file_fmp_key\n")
            f.write("POLYGON_KEY=file_polygon_key\n")
            f.write("FRED_KEY=file_fred_key\n")
            env_path = Path(f.name)

        try:
            config = Config.from_env(env_path)
            assert config.fmp.api_key == "file_fmp_key"
            assert config.polygon.api_key == "file_polygon_key"
            assert config.fred.api_key == "file_fred_key"
        finally:
            env_path.unlink()

    def test_invalid_log_level_defaults_to_info(self, clean_env):
        """Test that invalid log level defaults to INFO."""
        os.environ["LOG_LEVEL"] = "INVALID"
        config = Config.from_env()
        assert config.log_level == LogLevel.INFO

    def test_invalid_operating_mode_defaults_to_live(self, clean_env):
        """Test that invalid operating mode defaults to LIVE."""
        os.environ["OPERATING_MODE"] = "INVALID"
        config = Config.from_env()
        assert config.operating_mode == OperatingMode.LIVE

    def test_validate_missing_keys_in_live_mode(self, clean_env):
        """Test validation fails for missing API keys in LIVE mode."""
        config = Config.from_env()
        errors = config.validate()

        assert "FMP_KEY is required in LIVE mode" in errors
        assert "POLYGON_KEY is required in LIVE mode" in errors
        assert "FRED_KEY is required in LIVE mode" in errors

    def test_validate_passes_in_read_only_mode(self, clean_env):
        """Test validation passes without API keys in READ_ONLY mode."""
        os.environ["OPERATING_MODE"] = "READ_ONLY"
        config = Config.from_env()
        errors = config.validate()

        assert "FMP_KEY is required in LIVE mode" not in errors
        assert "POLYGON_KEY is required in LIVE mode" not in errors
        assert "FRED_KEY is required in LIVE mode" not in errors

    def test_validate_with_all_keys(self, clean_env):
        """Test validation passes with all API keys set."""
        os.environ["FMP_KEY"] = "key1"
        os.environ["POLYGON_KEY"] = "key2"
        os.environ["FRED_KEY"] = "key3"
        config = Config.from_env()
        errors = config.validate()

        assert config.is_valid()
        assert len(errors) == 0

    def test_validate_invalid_cache_ttl(self, clean_env):
        """Test validation fails for invalid cache TTL."""
        os.environ["FMP_KEY"] = "key1"
        os.environ["POLYGON_KEY"] = "key2"
        os.environ["FRED_KEY"] = "key3"
        os.environ["CACHE_TTL_DAYS"] = "0"
        config = Config.from_env()
        errors = config.validate()

        assert "CACHE_TTL_DAYS must be at least 1" in errors

    def test_get_cache_dir(self, clean_env):
        """Test getting provider-specific cache directories."""
        config = Config.from_env()

        fmp_cache = config.get_cache_dir("fmp")
        assert fmp_cache.name == "fmp_cache"

        polygon_cache = config.get_cache_dir("polygon")
        assert polygon_cache.name == "polygon_cache"

        fred_cache = config.get_cache_dir("fred")
        assert fred_cache.name == "fred_cache"

    def test_get_log_dir(self, clean_env):
        """Test getting logs directory."""
        config = Config.from_env()
        log_dir = config.get_log_dir()
        assert log_dir.name == "logs"

    def test_has_api_key(self, clean_env):
        """Test checking if API key is set."""
        os.environ["FMP_KEY"] = "test_key"
        config = Config.from_env()

        assert config.has_api_key("fmp") is True
        assert config.has_api_key("polygon") is False
        assert config.has_api_key("fred") is False

    def test_provider_base_urls(self, clean_env):
        """Test that provider base URLs are set correctly."""
        config = Config.from_env()

        assert config.fmp.base_url == "https://financialmodelingprep.com"
        assert config.polygon.base_url == "https://api.polygon.io"
        assert config.fred.base_url == "https://api.stlouisfed.org/fred"

    def test_provider_concurrency_limits(self, clean_env):
        """Test that provider concurrency limits are set correctly."""
        config = Config.from_env()

        assert config.fmp.max_concurrency == 3
        assert config.polygon.max_concurrency == 10
        assert config.fred.max_concurrency == 1


@pytest.mark.unit
class TestLoadConfig:
    """Tests for the load_config convenience function."""

    def test_load_config_returns_config(self, test_env):
        """Test that load_config returns a Config instance."""
        config = load_config()
        assert isinstance(config, Config)

    def test_load_config_with_path(self):
        """Test loading config from a specific path."""
        # Clean up environment first
        os.environ.pop("FMP_KEY", None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("FMP_KEY=path_test_key\n")
            env_path = Path(f.name)

        try:
            config = load_config(env_path)
            assert config.fmp.api_key == "path_test_key"
        finally:
            env_path.unlink()
            os.environ.pop("FMP_KEY", None)
