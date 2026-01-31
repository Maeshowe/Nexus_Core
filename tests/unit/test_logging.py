"""
Unit tests for the logging module.
"""

import logging
from pathlib import Path

import pytest

from data_loader.logging import (
    LoggerMixin,
    SanitizingFormatter,
    get_logger,
    sanitize_message,
    setup_logging,
)


@pytest.mark.unit
class TestSanitizingFormatter:
    """Tests for SanitizingFormatter class."""

    def test_sanitize_url_apikey(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request to https://api.example.com/data?apikey=abc123def456ghi789",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "abc123def456ghi789" not in formatted
        assert "[REDACTED]" in formatted

    def test_sanitize_url_api_key(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request to https://api.example.com/data?api_key=secret123",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "secret123" not in formatted
        assert "[REDACTED]" in formatted

    def test_sanitize_url_key_param(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request to https://api.example.com/data?key=myapikey",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "myapikey" not in formatted

    def test_sanitize_multiple_params(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="URL: https://api.example.com?apikey=key1&token=key2&other=value",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "key1" not in formatted
        assert "key2" not in formatted
        assert "other=value" in formatted  # Non-sensitive param preserved

    def test_sanitize_bearer_token(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in formatted
        assert "Bearer [REDACTED]" in formatted

    def test_sanitize_json_key_value(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Config: {"api_key": "secret123", "timeout": 30}',
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "secret123" not in formatted
        assert '"timeout": 30' in formatted or "timeout" in formatted

    def test_sanitize_long_hex_string(self):
        formatter = SanitizingFormatter()
        long_hex = "a" * 32 + "b" * 32  # 64 char hex string
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Token: {long_hex}",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert long_hex not in formatted
        assert "[REDACTED]" in formatted

    def test_preserve_normal_message(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Normal log message without secrets",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "Normal log message without secrets" in formatted

    def test_preserve_urls_without_keys(self):
        formatter = SanitizingFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Fetching from https://api.example.com/v1/data?symbol=AAPL",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "https://api.example.com/v1/data?symbol=AAPL" in formatted

    def test_additional_patterns(self):
        import re
        custom_pattern = (re.compile(r'SSN:\s*(\d{3}-\d{2}-\d{4})'), 'SSN: [REDACTED]')
        formatter = SanitizingFormatter(additional_patterns=[custom_pattern])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User SSN: 123-45-6789",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "123-45-6789" not in formatted


@pytest.mark.unit
class TestSanitizeMessage:
    """Tests for sanitize_message function."""

    def test_sanitize_api_key_in_url(self):
        message = "Calling https://api.fmp.com?apikey=abc123xyz"
        result = sanitize_message(message)
        assert "abc123xyz" not in result
        assert "[REDACTED]" in result

    def test_sanitize_multiple_keys(self):
        # Use URL format which the patterns are designed for
        message = "URL: https://api.com?apikey=secret1&token=secret2"
        result = sanitize_message(message)
        assert "secret1" not in result
        assert "secret2" not in result
        assert "[REDACTED]" in result

    def test_preserve_safe_content(self):
        message = "Processing symbol AAPL with timeout 30s"
        result = sanitize_message(message)
        assert result == message


@pytest.mark.unit
class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_console_only(self):
        logger = setup_logging(
            log_to_console=True,
            log_to_file=False,
            logger_name="test_console",
        )
        assert logger.name == "test_console"
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_file_only(self, temp_log_dir):
        logger = setup_logging(
            log_dir=temp_log_dir,
            log_to_console=False,
            log_to_file=True,
            logger_name="test_file",
        )
        assert logger.name == "test_file"
        assert len(logger.handlers) == 1
        assert (temp_log_dir / "test_file.log").exists()

    def test_setup_both_handlers(self, temp_log_dir):
        logger = setup_logging(
            log_dir=temp_log_dir,
            log_to_console=True,
            log_to_file=True,
            logger_name="test_both",
        )
        assert len(logger.handlers) == 2

    def test_setup_log_level(self):
        logger = setup_logging(
            log_level="DEBUG",
            log_to_file=False,
            logger_name="test_level",
        )
        assert logger.level == logging.DEBUG

    def test_setup_creates_log_dir(self, temp_log_dir):
        new_log_dir = temp_log_dir / "nested" / "logs"
        setup_logging(
            log_dir=new_log_dir,
            log_to_file=True,
            log_to_console=False,
            logger_name="test_nested",
        )
        assert new_log_dir.exists()

    def test_setup_clears_existing_handlers(self):
        logger = setup_logging(
            log_to_console=True,
            log_to_file=False,
            logger_name="test_clear",
        )
        original_handler = logger.handlers[0]

        # Setup again
        logger = setup_logging(
            log_to_console=True,
            log_to_file=False,
            logger_name="test_clear",
        )
        # Should only have one handler, not two
        assert len(logger.handlers) == 1

    def test_logging_sanitizes_output(self, temp_log_dir, capfd):
        logger = setup_logging(
            log_dir=temp_log_dir,
            log_to_console=True,
            log_to_file=True,
            log_level="INFO",
            logger_name="test_sanitize",
        )

        # Log a message with sensitive data
        logger.info("Request to https://api.example.com?apikey=super_secret_key_123")

        # Check console output (StreamHandler writes to stderr by default)
        captured = capfd.readouterr()
        console_output = captured.out + captured.err
        assert "super_secret_key_123" not in console_output
        assert "[REDACTED]" in console_output

        # Check file output
        log_file = temp_log_dir / "test_sanitize.log"
        content = log_file.read_text()
        assert "super_secret_key_123" not in content
        assert "[REDACTED]" in content


@pytest.mark.unit
class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_default_logger(self):
        logger = get_logger()
        assert logger.name == "nexus_core"

    def test_get_named_logger(self):
        logger = get_logger("custom_name")
        assert logger.name == "custom_name"

    def test_same_logger_returned(self):
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2


@pytest.mark.unit
class TestLoggerMixin:
    """Tests for LoggerMixin class."""

    def test_mixin_provides_logger(self):
        class TestClass(LoggerMixin):
            def do_something(self):
                return self.logger

        obj = TestClass()
        logger = obj.do_something()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "TestClass"

    def test_mixin_logger_cached(self):
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger1 = obj.logger
        logger2 = obj.logger
        assert logger1 is logger2

    def test_mixin_different_classes_different_loggers(self):
        class ClassA(LoggerMixin):
            pass

        class ClassB(LoggerMixin):
            pass

        a = ClassA()
        b = ClassB()
        assert a.logger.name == "ClassA"
        assert b.logger.name == "ClassB"
        assert a.logger is not b.logger
