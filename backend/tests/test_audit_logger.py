"""Tests for the audit logging service.

This module tests the AuditLogger functionality, including:
- Audit entry creation and storage
- API key redaction in audit logs
- Query functionality by session_id and timestamp
- Integration with route handlers
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from src.services.audit_logger import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditStatus,
    get_audit_logger,
    reset_audit_logger,
)
from src.utils.logging import REDACTED


class TestAuditEntry:
    """Tests for the AuditEntry dataclass."""

    def test_audit_entry_creation(self):
        """Test creating an audit entry with all fields."""
        entry = AuditEntry(
            event_type=AuditEventType.KEY_CONNECT,
            session_id="test-session-123",
            timestamp="2024-01-15T10:30:00Z",
            status=AuditStatus.SUCCESS,
            provider="openai",
            details={"action": "connect"},
            request_path="/auth/openai/connect",
            request_method="POST",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            error_message=None
        )

        assert entry.event_type == AuditEventType.KEY_CONNECT
        assert entry.session_id == "test-session-123"
        assert entry.status == AuditStatus.SUCCESS
        assert entry.provider == "openai"

    def test_audit_entry_to_dict_excludes_none(self):
        """Test that to_dict excludes None values."""
        entry = AuditEntry(
            event_type=AuditEventType.KEY_DISCONNECT,
            session_id="test-session",
            timestamp="2024-01-15T10:30:00Z",
            status=AuditStatus.SUCCESS,
            provider="claude",
            details=None,  # Should be excluded
            error_message=None  # Should be excluded
        )

        result = entry.to_dict()

        assert "event_type" in result
        assert "session_id" in result
        assert "details" not in result
        assert "error_message" not in result

    def test_audit_entry_to_json(self):
        """Test JSON serialization of audit entry."""
        entry = AuditEntry(
            event_type=AuditEventType.KEY_CONNECT,
            session_id="test-session",
            timestamp="2024-01-15T10:30:00Z",
            status=AuditStatus.SUCCESS,
            provider="openai"
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "key_connect"
        assert parsed["session_id"] == "test-session"
        assert parsed["status"] == "success"

    def test_audit_entry_enum_serialization(self):
        """Test that enum values are properly serialized."""
        entry = AuditEntry(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            session_id="test",
            timestamp="2024-01-15T10:30:00Z",
            status=AuditStatus.DENIED
        )

        result = entry.to_dict()

        assert result["event_type"] == "unauthorized_access"
        assert result["status"] == "denied"


class TestAuditLogger:
    """Tests for the AuditLogger class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset audit logger before each test."""
        reset_audit_logger()

    def test_log_key_connect_success(self):
        """Test logging a successful key connect operation."""
        logger = AuditLogger()

        entry = logger.log_key_connect(
            session_id="session-123",
            provider="openai",
            status=AuditStatus.SUCCESS
        )

        assert entry.event_type == AuditEventType.KEY_CONNECT
        assert entry.session_id == "session-123"
        assert entry.provider == "openai"
        assert entry.status == AuditStatus.SUCCESS
        assert entry.timestamp is not None

    def test_log_key_connect_failure(self):
        """Test logging a failed key connect operation."""
        logger = AuditLogger()

        entry = logger.log_key_connect(
            session_id="session-456",
            provider="claude",
            status=AuditStatus.FAILURE,
            error_message="Invalid API key"
        )

        assert entry.event_type == AuditEventType.KEY_CONNECT
        assert entry.status == AuditStatus.FAILURE
        assert entry.error_message == "Invalid API key"

    def test_log_key_connect_redacts_api_key_in_error(self):
        """Test that API keys in error messages are redacted."""
        logger = AuditLogger()

        entry = logger.log_key_connect(
            session_id="session-789",
            provider="openai",
            status=AuditStatus.FAILURE,
            error_message="Invalid key: sk-1234567890abcdef"
        )

        assert "sk-" not in entry.error_message
        assert REDACTED in entry.error_message

    def test_log_key_disconnect_success(self):
        """Test logging a successful key disconnect operation."""
        logger = AuditLogger()

        entry = logger.log_key_disconnect(
            session_id="session-abc",
            provider="claude",
            status=AuditStatus.SUCCESS
        )

        assert entry.event_type == AuditEventType.KEY_DISCONNECT
        assert entry.session_id == "session-abc"
        assert entry.status == AuditStatus.SUCCESS

    def test_log_key_disconnect_contains_timestamp(self):
        """Test that disconnect logs contain timestamp."""
        logger = AuditLogger()

        entry = logger.log_key_disconnect(
            session_id="session-xyz",
            provider="openai"
        )

        assert entry.timestamp is not None
        # Timestamp should be in ISO format with Z suffix
        assert entry.timestamp.endswith("Z")

    def test_log_unauthorized_access(self):
        """Test logging an unauthorized access attempt."""
        logger = AuditLogger()

        entry = logger.log_unauthorized_access(
            session_id="unknown-session",
            request_path="/auth/openai/disconnect",
            request_method="POST",
            client_ip="10.0.0.1",
            user_agent="curl/7.68.0",
            error_message="No API key connected"
        )

        assert entry.event_type == AuditEventType.UNAUTHORIZED_ACCESS
        assert entry.status == AuditStatus.DENIED
        assert entry.request_path == "/auth/openai/disconnect"
        assert entry.request_method == "POST"
        assert entry.client_ip == "10.0.0.1"

    def test_log_unauthorized_access_full_request_details(self):
        """Test that unauthorized access logs contain full request details."""
        logger = AuditLogger()

        entry = logger.log_unauthorized_access(
            session_id="test-session",
            request_path="/api/generate",
            request_method="POST",
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            details={
                "content_type": "application/json",
                "query_params": {"format": "json"}
            },
            error_message="Session expired"
        )

        assert entry.session_id == "test-session"
        assert entry.request_path == "/api/generate"
        assert entry.request_method == "POST"
        assert entry.client_ip == "192.168.1.100"
        assert entry.user_agent is not None
        assert entry.details is not None
        assert entry.error_message is not None

    def test_log_unauthorized_access_redacts_api_key_in_path(self):
        """Test that API keys in request paths are redacted."""
        logger = AuditLogger()

        entry = logger.log_unauthorized_access(
            session_id="test",
            request_path="/api?key=sk-ant-api03-abc123",
            request_method="GET"
        )

        assert "sk-ant-" not in entry.request_path
        assert REDACTED in entry.request_path


class TestAuditLoggerQueries:
    """Tests for audit log query functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset audit logger and create test data."""
        reset_audit_logger()

    def test_query_by_session(self):
        """Test querying audit entries by session ID."""
        logger = AuditLogger()

        # Create entries for different sessions
        logger.log_key_connect("session-A", "openai", AuditStatus.SUCCESS)
        logger.log_key_connect("session-B", "claude", AuditStatus.SUCCESS)
        logger.log_key_disconnect("session-A", "openai")

        results = logger.query_by_session("session-A")

        assert len(results) == 2
        assert all(e.session_id == "session-A" for e in results)

    def test_query_by_session_returns_empty_for_unknown(self):
        """Test that query returns empty list for unknown session."""
        logger = AuditLogger()
        logger.log_key_connect("known-session", "openai", AuditStatus.SUCCESS)

        results = logger.query_by_session("unknown-session")

        assert len(results) == 0

    def test_query_by_timestamp_range(self):
        """Test querying audit entries by timestamp range."""
        logger = AuditLogger()

        # Create some entries
        logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)
        logger.log_key_connect("session-2", "claude", AuditStatus.SUCCESS)

        # Query with a wide time range
        start_time = "2020-01-01T00:00:00Z"
        end_time = "2030-01-01T00:00:00Z"

        results = logger.query_by_timestamp_range(start_time, end_time)

        assert len(results) == 2

    def test_query_by_timestamp_range_excludes_outside(self):
        """Test that entries outside timestamp range are excluded."""
        logger = AuditLogger()

        # Create an entry
        entry = logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)

        # Query with a past time range
        start_time = "2020-01-01T00:00:00Z"
        end_time = "2020-12-31T23:59:59Z"

        results = logger.query_by_timestamp_range(start_time, end_time)

        # Entry should not be in results (it was created now, not in 2020)
        assert len(results) == 0

    def test_query_by_session_and_timestamp(self):
        """Test querying by both session ID and timestamp range."""
        logger = AuditLogger()

        # Create entries
        logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)
        logger.log_key_connect("session-2", "claude", AuditStatus.SUCCESS)

        start_time = "2020-01-01T00:00:00Z"
        end_time = "2030-01-01T00:00:00Z"

        results = logger.query_by_session_and_timestamp(
            "session-1", start_time, end_time
        )

        assert len(results) == 1
        assert results[0].session_id == "session-1"

    def test_get_all_entries(self):
        """Test retrieving all audit entries."""
        logger = AuditLogger()

        logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)
        logger.log_key_disconnect("session-1", "openai")
        logger.log_unauthorized_access("session-2", "/api/test", "GET")

        all_entries = logger.get_all_entries()

        assert len(all_entries) == 3

    def test_clear_entries(self):
        """Test clearing all audit entries."""
        logger = AuditLogger()

        logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)
        logger.log_key_connect("session-2", "claude", AuditStatus.SUCCESS)

        assert len(logger.get_all_entries()) == 2

        logger.clear_entries()

        assert len(logger.get_all_entries()) == 0


class TestAuditLoggerRedaction:
    """Tests for API key redaction in audit logs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset audit logger before each test."""
        reset_audit_logger()

    def test_redacts_openai_key_in_details(self):
        """Test that OpenAI API keys in details dict are redacted."""
        logger = AuditLogger()

        entry = logger.log_key_connect(
            session_id="test",
            provider="openai",
            status=AuditStatus.FAILURE,
            request_details={"api_key": "sk-1234567890abcdef1234567890"}
        )

        assert "sk-" not in str(entry.details)
        assert REDACTED in str(entry.details)

    def test_redacts_anthropic_key_in_details(self):
        """Test that Anthropic API keys in details dict are redacted."""
        logger = AuditLogger()

        entry = logger.log_key_connect(
            session_id="test",
            provider="claude",
            status=AuditStatus.FAILURE,
            request_details={"key": "sk-ant-api03-secret123"}
        )

        assert "sk-ant-" not in str(entry.details)
        assert REDACTED in str(entry.details)

    def test_redacts_api_key_in_user_agent(self):
        """Test that API keys accidentally in user agent are redacted."""
        logger = AuditLogger()

        entry = logger.log_unauthorized_access(
            session_id="test",
            request_path="/api/test",
            request_method="GET",
            user_agent="CustomClient/1.0 sk-1234567890abcdef"
        )

        assert "sk-" not in entry.user_agent
        assert REDACTED in entry.user_agent

    def test_audit_log_never_contains_actual_api_key(self):
        """Test comprehensive redaction - audit log should never contain API keys."""
        logger = AuditLogger()

        test_keys = [
            "sk-1234567890abcdefghijklmnop",
            "sk-ant-api03-abcdefghijklmnop",
            "sk-proj-abc123xyz"
        ]

        for key in test_keys:
            entry = logger.log_key_connect(
                session_id=f"session-with-{key}",
                provider="test",
                status=AuditStatus.FAILURE,
                error_message=f"Failed with key {key}",
                request_details={
                    "api_key": key,
                    "nested": {"secret": key}
                }
            )

            # Check JSON representation
            json_repr = entry.to_json()
            assert key not in json_repr, f"API key {key[:10]}... found in audit log JSON"

            # Check dict representation
            dict_repr = str(entry.to_dict())
            assert key not in dict_repr, f"API key {key[:10]}... found in audit log dict"


class TestGlobalAuditLogger:
    """Tests for the global audit logger singleton."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset global audit logger before each test."""
        reset_audit_logger()

    def test_get_audit_logger_returns_same_instance(self):
        """Test that get_audit_logger returns the same instance."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

    def test_reset_audit_logger_creates_new_instance(self):
        """Test that reset_audit_logger creates a new instance."""
        logger1 = get_audit_logger()
        logger1.log_key_connect("test", "openai", AuditStatus.SUCCESS)

        reset_audit_logger()

        logger2 = get_audit_logger()
        assert len(logger2.get_all_entries()) == 0


class TestAuditLoggerIntegration:
    """Integration tests for audit logger with routes."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset audit logger before each test."""
        reset_audit_logger()

    def test_connect_operation_audit_entry_format(self):
        """Test that connect operation creates properly formatted audit entry."""
        logger = get_audit_logger()

        entry = logger.log_key_connect(
            session_id="integration-test-session",
            provider="openai",
            status=AuditStatus.SUCCESS
        )

        # Verify acceptance criteria: contains session_id, timestamp, status
        assert entry.session_id == "integration-test-session"
        assert entry.timestamp is not None
        assert entry.status == AuditStatus.SUCCESS

        # Verify JSON format for persistence
        json_data = json.loads(entry.to_json())
        assert "session_id" in json_data
        assert "timestamp" in json_data
        assert "status" in json_data

    def test_disconnect_operation_audit_entry_format(self):
        """Test that disconnect operation creates properly formatted audit entry."""
        logger = get_audit_logger()

        entry = logger.log_key_disconnect(
            session_id="disconnect-test-session",
            provider="claude"
        )

        # Verify acceptance criteria: contains session_id, timestamp
        assert entry.session_id == "disconnect-test-session"
        assert entry.timestamp is not None

        json_data = json.loads(entry.to_json())
        assert "session_id" in json_data
        assert "timestamp" in json_data

    def test_unauthorized_access_audit_entry_format(self):
        """Test that unauthorized access creates properly formatted audit entry."""
        logger = get_audit_logger()

        entry = logger.log_unauthorized_access(
            session_id="unauthorized-session",
            request_path="/auth/openai/disconnect",
            request_method="POST",
            client_ip="192.168.1.100",
            user_agent="TestClient/1.0",
            details={"headers": {"Accept": "application/json"}},
            error_message="No key connected"
        )

        # Verify acceptance criteria: contains full request details
        assert entry.session_id == "unauthorized-session"
        assert entry.request_path == "/auth/openai/disconnect"
        assert entry.request_method == "POST"
        assert entry.client_ip == "192.168.1.100"
        assert entry.user_agent == "TestClient/1.0"
        assert entry.details is not None

        json_data = json.loads(entry.to_json())
        assert "request_path" in json_data
        assert "request_method" in json_data
        assert "client_ip" in json_data

    def test_audit_entries_queryable_by_session_id(self):
        """Test acceptance criteria: audit logs queryable by session_id."""
        logger = get_audit_logger()

        # Create entries for multiple sessions
        logger.log_key_connect("session-alpha", "openai", AuditStatus.SUCCESS)
        logger.log_key_disconnect("session-alpha", "openai")
        logger.log_key_connect("session-beta", "claude", AuditStatus.FAILURE)
        logger.log_unauthorized_access("session-gamma", "/api", "GET")

        # Query by specific session
        alpha_entries = logger.query_by_session("session-alpha")

        assert len(alpha_entries) == 2
        assert all(e.session_id == "session-alpha" for e in alpha_entries)

    def test_audit_entries_queryable_by_timestamp_range(self):
        """Test acceptance criteria: audit logs queryable by timestamp range."""
        logger = get_audit_logger()

        # Create some entries
        logger.log_key_connect("session-1", "openai", AuditStatus.SUCCESS)
        logger.log_key_connect("session-2", "claude", AuditStatus.SUCCESS)

        # Get current timestamp range that includes now
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=1)).isoformat() + "Z"
        end = (now + timedelta(hours=1)).isoformat() + "Z"

        # Query by timestamp range
        entries = logger.query_by_timestamp_range(start, end)

        assert len(entries) == 2
