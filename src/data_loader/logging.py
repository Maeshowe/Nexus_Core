"""
OmniData Nexus Core - Logging Module

Provides logging configuration with API key sanitization.
All log output automatically redacts sensitive information.
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class SanitizingFormatter(logging.Formatter):
    """
    Log formatter that sanitizes sensitive information.

    Automatically redacts:
    - API keys in URLs (apikey=..., api_key=..., key=...)
    - API keys passed as parameters
    - Bearer tokens
    - Common secret patterns

    Usage:
        formatter = SanitizingFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
    """

    # Patterns to match and redact
    PATTERNS = [
        # URL query parameters (case-insensitive)
        (re.compile(r'([\?&])(api[_-]?key|apikey|key|token)=([^&\s]+)', re.IGNORECASE), r'\1\2=[REDACTED]'),
        # JSON/dict key-value pairs
        (re.compile(r'(["\'])(api[_-]?key|apikey|key|token|secret|password)(["\'])\s*[:=]\s*(["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1\2\3:\4[REDACTED]\6'),
        # Bearer tokens
        (re.compile(r'(Bearer\s+)([A-Za-z0-9\-_\.]+)', re.IGNORECASE), r'\1[REDACTED]'),
        # Standalone API key patterns (32+ hex chars)
        (re.compile(r'\b([a-fA-F0-9]{32,})\b'), r'[REDACTED]'),
        # Known provider key patterns (adjust based on actual key formats)
        (re.compile(r'\b([a-zA-Z0-9]{20,}[a-zA-Z0-9\-_\.]*)\b'), lambda m: _redact_if_key_like(m)),
    ]

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        additional_patterns: Optional[list[tuple]] = None,
    ):
        """
        Initialize sanitizing formatter.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            style: Format style ('%', '{', or '$')
            additional_patterns: Additional (pattern, replacement) tuples to apply
        """
        super().__init__(fmt, datefmt, style)
        self.additional_patterns = additional_patterns or []

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sanitization."""
        # Format the message first
        formatted = super().format(record)

        # Apply sanitization patterns
        for pattern, replacement in self.PATTERNS:
            if callable(replacement):
                formatted = pattern.sub(replacement, formatted)
            else:
                formatted = pattern.sub(replacement, formatted)

        # Apply additional patterns
        for pattern, replacement in self.additional_patterns:
            formatted = pattern.sub(replacement, formatted)

        return formatted


def _redact_if_key_like(match: re.Match) -> str:
    """
    Check if a matched string looks like an API key and redact if so.

    Heuristics:
    - Contains mix of letters and numbers
    - Doesn't look like a common word or path
    - Length suggests it could be a key
    """
    value = match.group(1)

    # Skip if it looks like a common word or path
    skip_patterns = [
        r'^https?://',  # URLs
        r'^/[a-z]',  # File paths
        r'^[a-z]+_[a-z]+$',  # snake_case identifiers
        r'^[a-z]+[A-Z][a-z]+',  # camelCase identifiers
        r'^\d+$',  # Pure numbers
    ]

    for skip in skip_patterns:
        if re.match(skip, value):
            return value

    # Check if it has characteristics of an API key
    has_upper = any(c.isupper() for c in value)
    has_lower = any(c.islower() for c in value)
    has_digit = any(c.isdigit() for c in value)

    # Looks like a key if it has mixed case and numbers, or is very long
    if (has_upper and has_lower and has_digit) or len(value) > 40:
        return '[REDACTED]'

    return value


def sanitize_message(message: str) -> str:
    """
    Sanitize a message string by redacting sensitive information.

    This function can be used standalone without a logger.

    Args:
        message: Message to sanitize

    Returns:
        Sanitized message with sensitive data redacted
    """
    result = message

    for pattern, replacement in SanitizingFormatter.PATTERNS:
        if callable(replacement):
            result = pattern.sub(replacement, result)
        else:
            result = pattern.sub(replacement, result)

    return result


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    logger_name: str = "nexus_core",
) -> logging.Logger:
    """
    Set up logging for the application.

    Configures both console and file logging with API key sanitization.

    Args:
        log_dir: Directory for log files (default: ./logs)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
        logger_name: Name of the logger

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Create sanitizing formatter
    formatter = SanitizingFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        if log_dir is None:
            log_dir = Path.cwd() / "logs"

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{logger_name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "nexus_core") -> logging.Logger:
    """
    Get a logger instance.

    If the logger hasn't been set up yet, returns a basic logger.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.

    Usage:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
