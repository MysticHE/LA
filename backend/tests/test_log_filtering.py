"""Tests for API key log filtering.

Tests verify that API keys are properly redacted from all log output.
"""

import logging
import pytest
from io import StringIO

from src.utils.logging import (
    redact_api_keys,
    redact_dict_values,
    APIKeyRedactionFilter,
    get_secure_logger,
    configure_root_logger,
    REDACTED,
)
from src.middleware.request_logging import (
    log_request_body,
    log_message,
)


class TestRedactApiKeys:
    """Tests for the redact_api_keys function."""

    def test_redacts_openai_sk_pattern(self):
        """GIVEN a string with 'sk-' pattern WHEN redact_api_keys THEN replace with [REDACTED]."""
        text = "Using key: sk-abc123xyz"
        result = redact_api_keys(text)
        assert result == f"Using key: {REDACTED}"

    def test_redacts_anthropic_sk_ant_pattern(self):
        """GIVEN a string with 'sk-ant-' pattern WHEN redact_api_keys THEN replace with [REDACTED]."""
        text = "Claude key: sk-ant-api03-abcdefg12345"
        result = redact_api_keys(text)
        assert result == f"Claude key: {REDACTED}"

    def test_redacts_multiple_keys(self):
        """GIVEN a string with multiple API keys WHEN redact_api_keys THEN all are redacted."""
        text = "Keys: sk-abc123 and sk-ant-xyz789"
        result = redact_api_keys(text)
        assert "sk-" not in result
        assert result.count(REDACTED) == 2

    def test_preserves_non_key_text(self):
        """GIVEN a string without API keys WHEN redact_api_keys THEN text is preserved."""
        text = "This is normal text without any keys"
        result = redact_api_keys(text)
        assert result == text

    def test_handles_empty_string(self):
        """GIVEN an empty string WHEN redact_api_keys THEN returns empty string."""
        result = redact_api_keys("")
        assert result == ""

    def test_redacts_key_at_start(self):
        """GIVEN API key at start of string WHEN redact_api_keys THEN redacted."""
        text = "sk-abc123 is the key"
        result = redact_api_keys(text)
        assert result.startswith(REDACTED)

    def test_redacts_key_at_end(self):
        """GIVEN API key at end of string WHEN redact_api_keys THEN redacted."""
        text = "The key is sk-abc123"
        result = redact_api_keys(text)
        assert result.endswith(REDACTED)

    def test_redacts_key_in_json(self):
        """GIVEN API key in JSON-like string WHEN redact_api_keys THEN redacted."""
        text = '{"api_key": "sk-abc123", "name": "test"}'
        result = redact_api_keys(text)
        assert "sk-" not in result
        assert REDACTED in result

    def test_redacts_key_with_underscores_and_dashes(self):
        """GIVEN API key with special chars WHEN redact_api_keys THEN redacted."""
        text = "Key: sk-proj_abc-123_xyz"
        result = redact_api_keys(text)
        assert "sk-" not in result

    def test_redacts_long_key(self):
        """GIVEN a long API key WHEN redact_api_keys THEN completely redacted."""
        long_key = "sk-" + "a" * 100
        result = redact_api_keys(long_key)
        assert result == REDACTED


class TestRedactDictValues:
    """Tests for the redact_dict_values function."""

    def test_redacts_api_key_field(self):
        """GIVEN structured logging WHEN api_key field exists THEN field value is redacted."""
        data = {"api_key": "sk-secret123", "name": "test"}
        result = redact_dict_values(data)
        assert result["api_key"] == REDACTED
        assert result["name"] == "test"

    def test_redacts_key_field(self):
        """GIVEN dict with 'key' field WHEN redact_dict_values THEN redacted."""
        data = {"key": "sk-abc123"}
        result = redact_dict_values(data)
        assert result["key"] == REDACTED

    def test_redacts_secret_field(self):
        """GIVEN dict with 'secret' field WHEN redact_dict_values THEN redacted."""
        data = {"secret": "my-secret-value"}
        result = redact_dict_values(data)
        assert result["secret"] == REDACTED

    def test_redacts_nested_api_key(self):
        """GIVEN nested dict with api_key WHEN redact_dict_values THEN redacted."""
        data = {"config": {"api_key": "sk-nested123"}}
        result = redact_dict_values(data)
        assert result["config"]["api_key"] == REDACTED

    def test_redacts_api_key_in_string_values(self):
        """GIVEN dict with API key in string value WHEN redact_dict_values THEN redacted."""
        data = {"message": "Using key sk-abc123 for request"}
        result = redact_dict_values(data)
        assert "sk-" not in result["message"]
        assert REDACTED in result["message"]

    def test_redacts_api_key_in_list(self):
        """GIVEN dict with list containing API key WHEN redact_dict_values THEN redacted."""
        data = {"keys": ["sk-key1", "sk-key2"]}
        result = redact_dict_values(data)
        assert all("sk-" not in k for k in result["keys"])

    def test_preserves_non_sensitive_data(self):
        """GIVEN dict without sensitive data WHEN redact_dict_values THEN preserved."""
        data = {"name": "test", "count": 42, "enabled": True}
        result = redact_dict_values(data)
        assert result == data

    def test_handles_empty_dict(self):
        """GIVEN empty dict WHEN redact_dict_values THEN returns empty dict."""
        result = redact_dict_values({})
        assert result == {}

    def test_custom_sensitive_fields(self):
        """GIVEN custom sensitive fields WHEN redact_dict_values THEN those are redacted."""
        data = {"custom_field": "sensitive", "other": "value"}
        result = redact_dict_values(data, sensitive_fields={"custom_field"})
        assert result["custom_field"] == REDACTED
        assert result["other"] == "value"


class TestAPIKeyRedactionFilter:
    """Tests for the logging filter."""

    def test_redacts_message_with_sk_pattern(self):
        """GIVEN log with 'sk-' pattern WHEN filter applied THEN message redacted."""
        filter_obj = APIKeyRedactionFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="API key: sk-abc123",
            args=(),
            exc_info=None
        )
        filter_obj.filter(record)
        assert "sk-" not in record.msg
        assert REDACTED in record.msg

    def test_redacts_message_with_sk_ant_pattern(self):
        """GIVEN log with 'sk-ant-' pattern WHEN filter applied THEN message redacted."""
        filter_obj = APIKeyRedactionFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Anthropic key: sk-ant-abc123xyz",
            args=(),
            exc_info=None
        )
        filter_obj.filter(record)
        assert "sk-ant-" not in record.msg
        assert REDACTED in record.msg

    def test_redacts_tuple_args(self):
        """GIVEN log with tuple args containing API key WHEN filter THEN redacted."""
        filter_obj = APIKeyRedactionFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Key: %s",
            args=("sk-abc123",),
            exc_info=None
        )
        filter_obj.filter(record)
        assert "sk-" not in record.args[0]

    def test_redacts_dict_args(self):
        """GIVEN log with dict args containing api_key field WHEN filter THEN redacted."""
        filter_obj = APIKeyRedactionFilter()
        # Create a basic log record and manually set args to a dict
        # (LogRecord constructor in Python 3.14+ has issues with dict args)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Data: %(api_key)s",
            args=(),
            exc_info=None
        )
        # Manually set dict args after construction
        record.args = {"api_key": "sk-abc123"}
        filter_obj.filter(record)
        assert record.args["api_key"] == REDACTED

    def test_allows_record_through(self):
        """GIVEN any log record WHEN filter applied THEN returns True (allows logging)."""
        filter_obj = APIKeyRedactionFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Normal message",
            args=(),
            exc_info=None
        )
        result = filter_obj.filter(record)
        assert result is True

    def test_handles_non_string_message(self):
        """GIVEN log with non-string message WHEN filter applied THEN no error."""
        filter_obj = APIKeyRedactionFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=123,  # Non-string message
            args=(),
            exc_info=None
        )
        # Should not raise
        result = filter_obj.filter(record)
        assert result is True


class TestGetSecureLogger:
    """Tests for get_secure_logger function."""

    def test_returns_logger_with_filter(self):
        """GIVEN call to get_secure_logger WHEN called THEN returns logger with filter."""
        logger = get_secure_logger("test_secure")
        has_filter = any(isinstance(f, APIKeyRedactionFilter) for f in logger.filters)
        assert has_filter

    def test_logger_redacts_api_keys(self):
        """GIVEN secure logger WHEN log contains API key THEN redacted in output."""
        # Create logger with handler to capture output
        logger = get_secure_logger("test_redact_output")
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.addFilter(APIKeyRedactionFilter())
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Using key: sk-abc123xyz")
        output = stream.getvalue()

        assert "sk-" not in output
        assert REDACTED in output


class TestMiddlewareFunctions:
    """Tests for middleware helper functions."""

    def test_log_request_body_redacts_api_key(self):
        """GIVEN request body with api_key WHEN log_request_body THEN redacted."""
        body = {"api_key": "sk-secret123", "prompt": "Hello"}
        result = log_request_body(body)
        assert result["api_key"] == REDACTED
        assert result["prompt"] == "Hello"

    def test_log_message_redacts_sk_pattern(self):
        """GIVEN message with sk- pattern WHEN log_message THEN redacted."""
        message = "Request with sk-abc123"
        result = log_message(message)
        assert "sk-" not in result
        assert REDACTED in result

    def test_log_message_redacts_sk_ant_pattern(self):
        """GIVEN message with sk-ant- pattern WHEN log_message THEN redacted."""
        message = "Using sk-ant-api03-xyz789"
        result = log_message(message)
        assert "sk-ant-" not in result
        assert REDACTED in result


class TestConfigureRootLogger:
    """Tests for configure_root_logger function."""

    def test_adds_filter_to_root_logger(self):
        """GIVEN configure_root_logger WHEN called THEN root logger has filter."""
        # Store original filters
        root_logger = logging.getLogger()
        original_filters = list(root_logger.filters)

        try:
            configure_root_logger()
            has_filter = any(isinstance(f, APIKeyRedactionFilter) for f in root_logger.filters)
            assert has_filter
        finally:
            # Restore original state
            root_logger.filters = original_filters


class TestEdgeCases:
    """Edge case tests for comprehensive coverage."""

    def test_partial_sk_prefix_not_redacted(self):
        """GIVEN text with 'sk' without dash WHEN redact THEN not redacted."""
        text = "The task was completed"
        result = redact_api_keys(text)
        assert result == text

    def test_sk_with_minimal_suffix_is_redacted(self):
        """GIVEN 'sk-' with minimal suffix WHEN redact THEN key redacted."""
        text = "Key: sk-x"
        result = redact_api_keys(text)
        # Real API keys always have characters after sk-
        assert result == f"Key: {REDACTED}"
        assert "sk-" not in result

    def test_multiple_keys_different_types(self):
        """GIVEN multiple different key types WHEN redact THEN all redacted."""
        text = "OpenAI: sk-openai123, Claude: sk-ant-claude456"
        result = redact_api_keys(text)
        assert result.count(REDACTED) == 2
        assert "sk-" not in result

    def test_case_sensitive_pattern(self):
        """GIVEN uppercase SK- WHEN redact THEN not redacted (case sensitive)."""
        text = "Upper: SK-ABC123"
        result = redact_api_keys(text)
        # Our pattern is case sensitive, uppercase should not match
        assert "SK-ABC123" in result

    def test_deeply_nested_dict(self):
        """GIVEN deeply nested dict WHEN redact_dict_values THEN all levels redacted."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "api_key": "sk-deep123"
                    }
                }
            }
        }
        result = redact_dict_values(data)
        assert result["level1"]["level2"]["level3"]["api_key"] == REDACTED

    def test_mixed_list_in_dict(self):
        """GIVEN dict with mixed type list WHEN redact_dict_values THEN handles all."""
        data = {
            "items": [
                {"api_key": "sk-in-dict"},
                "sk-in-string",
                123,
                None
            ]
        }
        result = redact_dict_values(data)
        assert result["items"][0]["api_key"] == REDACTED
        assert REDACTED in result["items"][1]
        assert result["items"][2] == 123
        assert result["items"][3] is None
