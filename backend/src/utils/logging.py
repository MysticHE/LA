"""Secure logging utilities with API key redaction.

This module provides logging functionality that automatically redacts
sensitive API keys from log output to prevent credential exposure.
"""

import logging
import re
from typing import Any, Optional


# Patterns that match common API key formats
# Matches: sk-... (OpenAI), sk-ant-... (Anthropic), AIza... (Google/Gemini), and similar patterns
API_KEY_PATTERNS = [
    re.compile(r'sk-ant-[a-zA-Z0-9_-]+'),  # Anthropic keys (more specific, match first)
    re.compile(r'sk-[a-zA-Z0-9_-]+'),       # OpenAI and generic sk- keys
    re.compile(r'AIza[a-zA-Z0-9_-]{35,}'),  # Google/Gemini API keys (start with AIza, 39+ chars total)
]

REDACTED = '[REDACTED]'


def mask_api_key(api_key: str) -> str:
    """Mask an API key, showing only the last 4 characters.

    Args:
        api_key: The API key to mask.

    Returns:
        Masked key in format ****xxxx where xxxx is last 4 characters.
        Returns "****" for keys with 4 or fewer characters.
    """
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "****"
    return "*" * (len(api_key) - 4) + api_key[-4:]


def redact_api_keys(text: str) -> str:
    """Redact API keys from text.

    Args:
        text: The text that may contain API keys.

    Returns:
        Text with all API keys replaced with [REDACTED].
    """
    result = text
    for pattern in API_KEY_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


def redact_dict_values(data: dict, sensitive_fields: Optional[set] = None) -> dict:
    """Redact sensitive values from a dictionary.

    Recursively processes nested dictionaries and lists.

    Args:
        data: Dictionary that may contain sensitive values.
        sensitive_fields: Set of field names to always redact.
                         Defaults to {'api_key', 'api_keys', 'key', 'secret'}.

    Returns:
        Dictionary with sensitive values redacted.
    """
    if sensitive_fields is None:
        sensitive_fields = {'api_key', 'api_keys', 'key', 'secret', 'password', 'token'}

    result = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            result[key] = REDACTED
        elif isinstance(value, dict):
            result[key] = redact_dict_values(value, sensitive_fields)
        elif isinstance(value, list):
            result[key] = [
                redact_dict_values(item, sensitive_fields) if isinstance(item, dict)
                else redact_api_keys(str(item)) if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = redact_api_keys(value)
        else:
            result[key] = value
    return result


class APIKeyRedactionFilter(logging.Filter):
    """Logging filter that redacts API keys from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to redact API keys.

        Args:
            record: The log record to process.

        Returns:
            True (always allows the record through after redaction).
        """
        # Redact the main message
        if isinstance(record.msg, str):
            record.msg = redact_api_keys(record.msg)

        # Redact arguments if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_dict_values(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_api_keys(str(arg)) if isinstance(arg, str)
                    else redact_dict_values(arg) if isinstance(arg, dict)
                    else arg
                    for arg in record.args
                )

        return True


def get_secure_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a logger with API key redaction enabled.

    Args:
        name: The logger name (typically __name__).
        level: The logging level. Defaults to INFO.

    Returns:
        Logger configured with API key redaction filter.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add redaction filter if not already present
    has_redaction_filter = any(
        isinstance(f, APIKeyRedactionFilter) for f in logger.filters
    )
    if not has_redaction_filter:
        logger.addFilter(APIKeyRedactionFilter())

    return logger


def configure_root_logger(level: int = logging.INFO) -> None:
    """Configure the root logger with API key redaction.

    This should be called at application startup to ensure all
    loggers inherit the redaction filter.

    Args:
        level: The logging level. Defaults to INFO.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Add redaction filter to root logger
    has_redaction_filter = any(
        isinstance(f, APIKeyRedactionFilter) for f in root_logger.filters
    )
    if not has_redaction_filter:
        root_logger.addFilter(APIKeyRedactionFilter())

    # Also add to all handlers
    for handler in root_logger.handlers:
        has_handler_filter = any(
            isinstance(f, APIKeyRedactionFilter) for f in handler.filters
        )
        if not has_handler_filter:
            handler.addFilter(APIKeyRedactionFilter())
