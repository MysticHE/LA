"""Tests for audit logging service.

Tests cover all acceptance criteria for US-SEC-004:
1. API key connect/disconnect creates audit log with timestamp and session ID
2. Image generation creates audit log with request metadata
3. Audit logs contain no sensitive data (API keys, prompt content)
4. Audit logs support filtering by date and session
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.services.audit_logger import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditStatus,
    get_audit_logger,
    reset_audit_logger,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def audit_logger():
    """Create a fresh AuditLogger instance for each test."""
    return AuditLogger("test")


@pytest.fixture
def reset_global_logger():
    """Reset the global audit logger before and after each test."""
    reset_audit_logger()
    yield
    reset_audit_logger()


# =============================================================================
# AC1: API Key Connect/Disconnect Audit Logging
# =============================================================================

class TestKeyConnectDisconnectAudit:
    """Tests for audit logging of API key connect/disconnect operations."""

    def test_key_connect_creates_audit_log(self, audit_logger):
        """GIVEN API key connect WHEN action completes THEN audit log created."""
        entry = audit_logger.log_key_connect(
            session_id="test-session-123",
            provider="gemini",
            status=AuditStatus.SUCCESS
        )

        assert entry is not None
        assert entry.event_type == AuditEventType.KEY_CONNECT
        assert entry.session_id == "test-session-123"
        assert entry.provider == "gemini"
        assert entry.status == AuditStatus.SUCCESS

    def test_key_connect_includes_timestamp(self, audit_logger):
        """GIVEN API key connect WHEN action completes THEN audit log has timestamp."""
        entry = audit_logger.log_key_connect(
            session_id="test-session-123",
            provider="openai",
            status=AuditStatus.SUCCESS
        )

        assert entry.timestamp is not None
        # Verify it's a valid ISO format timestamp
        timestamp = entry.timestamp
        assert "T" in timestamp
        assert timestamp.endswith("Z")

    def test_key_connect_includes_session_id(self, audit_logger):
        """GIVEN API key connect WHEN action completes THEN audit log has session ID."""
        entry = audit_logger.log_key_connect(
            session_id="session-abc-xyz",
            provider="claude",
            status=AuditStatus.SUCCESS
        )

        assert entry.session_id == "session-abc-xyz"

    def test_key_disconnect_creates_audit_log(self, audit_logger):
        """GIVEN API key disconnect WHEN action completes THEN audit log created."""
        entry = audit_logger.log_key_disconnect(
            session_id="test-session-456",
            provider="gemini"
        )

        assert entry is not None
        assert entry.event_type == AuditEventType.KEY_DISCONNECT
        assert entry.session_id == "test-session-456"
        assert entry.provider == "gemini"
        assert entry.status == AuditStatus.SUCCESS

    def test_key_disconnect_includes_timestamp(self, audit_logger):
        """GIVEN API key disconnect WHEN action completes THEN audit log has timestamp."""
        entry = audit_logger.log_key_disconnect(
            session_id="test-session-456",
            provider="openai"
        )

        assert entry.timestamp is not None
        assert "T" in entry.timestamp
        assert entry.timestamp.endswith("Z")

    def test_key_disconnect_includes_session_id(self, audit_logger):
        """GIVEN API key disconnect WHEN action completes THEN audit log has session ID."""
        entry = audit_logger.log_key_disconnect(
            session_id="session-disconnect-test",
            provider="claude"
        )

        assert entry.session_id == "session-disconnect-test"

    def test_key_connect_failed_logs_error(self, audit_logger):
        """GIVEN API key connect failure WHEN logged THEN includes error message."""
        entry = audit_logger.log_key_connect(
            session_id="test-session-789",
            provider="gemini",
            status=AuditStatus.FAILURE,
            error_message="Invalid API key"
        )

        assert entry.status == AuditStatus.FAILURE
        assert entry.error_message == "Invalid API key"

    def test_key_operations_stored_in_order(self, audit_logger):
        """GIVEN multiple key operations WHEN logged THEN stored in order."""
        audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)
        audit_logger.log_key_connect("session-2", "openai", AuditStatus.SUCCESS)
        audit_logger.log_key_disconnect("session-1", "gemini")

        entries = audit_logger.get_all_entries()
        assert len(entries) == 3
        assert entries[0].session_id == "session-1"
        assert entries[0].event_type == AuditEventType.KEY_CONNECT
        assert entries[1].session_id == "session-2"
        assert entries[2].event_type == AuditEventType.KEY_DISCONNECT


# =============================================================================
# AC2: Image Generation Audit Logging
# =============================================================================

class TestImageGenerationAudit:
    """Tests for audit logging of image generation operations."""

    def test_image_generation_creates_audit_log(self, audit_logger):
        """GIVEN image generation WHEN completed THEN audit log created."""
        entry = audit_logger.log_image_generation(
            session_id="img-session-123",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            style="minimalist",
            content_type="TUTORIAL"
        )

        assert entry is not None
        assert entry.event_type == AuditEventType.IMAGE_GENERATION
        assert entry.status == AuditStatus.SUCCESS

    def test_image_generation_includes_request_metadata(self, audit_logger):
        """GIVEN image generation WHEN completed THEN audit log has request metadata."""
        entry = audit_logger.log_image_generation(
            session_id="img-session-456",
            status=AuditStatus.SUCCESS,
            dimensions="1080x1080",
            style="infographic",
            content_type="ANNOUNCEMENT"
        )

        assert entry.details is not None
        assert entry.details["dimensions"] == "1080x1080"
        assert entry.details["style"] == "infographic"
        assert entry.details["content_type"] == "ANNOUNCEMENT"

    def test_image_generation_includes_timestamp(self, audit_logger):
        """GIVEN image generation WHEN completed THEN audit log has timestamp."""
        entry = audit_logger.log_image_generation(
            session_id="img-session-789",
            status=AuditStatus.SUCCESS,
            dimensions="1200x1200"
        )

        assert entry.timestamp is not None
        assert "T" in entry.timestamp
        assert entry.timestamp.endswith("Z")

    def test_image_generation_includes_session_id(self, audit_logger):
        """GIVEN image generation WHEN completed THEN audit log has session ID."""
        entry = audit_logger.log_image_generation(
            session_id="specific-session-id",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627"
        )

        assert entry.session_id == "specific-session-id"

    def test_image_generation_failure_logs_error(self, audit_logger):
        """GIVEN image generation failure WHEN logged THEN includes error message."""
        entry = audit_logger.log_image_generation(
            session_id="fail-session",
            status=AuditStatus.FAILURE,
            dimensions="1200x627",
            error_message="Rate limit exceeded"
        )

        assert entry.status == AuditStatus.FAILURE
        assert entry.error_message == "Rate limit exceeded"

    def test_image_generation_logs_provider(self, audit_logger):
        """GIVEN image generation WHEN logged THEN includes provider (gemini)."""
        entry = audit_logger.log_image_generation(
            session_id="provider-test",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627"
        )

        assert entry.provider == "gemini"

    def test_image_generation_additional_metadata(self, audit_logger):
        """GIVEN image generation with metadata WHEN logged THEN includes safe metadata."""
        entry = audit_logger.log_image_generation(
            session_id="metadata-test",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            request_metadata={"retry_after": 60, "request_id": "req-123"}
        )

        assert entry.details is not None
        assert entry.details.get("retry_after") == 60
        assert entry.details.get("request_id") == "req-123"


# =============================================================================
# AC3: No Sensitive Data in Audit Logs
# =============================================================================

class TestNoSensitiveDataInLogs:
    """Tests verifying audit logs contain no sensitive data."""

    def test_api_keys_redacted_from_session_id(self, audit_logger):
        """GIVEN session ID with API key WHEN logged THEN key is redacted."""
        # OpenAI-style key in session ID
        entry = audit_logger.log_key_connect(
            session_id="session-sk-abc123xyz789def456ghi012",
            provider="openai",
            status=AuditStatus.SUCCESS
        )

        assert "sk-" not in entry.session_id
        assert "[REDACTED]" in entry.session_id

    def test_api_keys_redacted_from_error_message(self, audit_logger):
        """GIVEN error message with API key WHEN logged THEN key is redacted."""
        entry = audit_logger.log_key_connect(
            session_id="test-session",
            provider="openai",
            status=AuditStatus.FAILURE,
            error_message="Failed with key sk-test123abc456def789"
        )

        assert "sk-test" not in entry.error_message
        assert "[REDACTED]" in entry.error_message

    def test_anthropic_keys_redacted(self, audit_logger):
        """GIVEN Anthropic API key WHEN logged THEN key is redacted."""
        entry = audit_logger.log_key_connect(
            session_id="session-with-sk-ant-abc123xyz789",
            provider="claude",
            status=AuditStatus.FAILURE,
            error_message="Key sk-ant-secret123 is invalid"
        )

        assert "sk-ant-" not in entry.session_id
        assert "sk-ant-" not in entry.error_message
        assert "[REDACTED]" in entry.session_id
        assert "[REDACTED]" in entry.error_message

    def test_gemini_keys_redacted(self, audit_logger):
        """GIVEN Gemini API key WHEN logged THEN key is redacted."""
        # Gemini keys start with AIza and are 39+ characters
        gemini_key = "AIzaSyC123456789abcdefghijklmnopqrstuvwxy"
        entry = audit_logger.log_key_connect(
            session_id=f"session-{gemini_key}",
            provider="gemini",
            status=AuditStatus.FAILURE,
            error_message=f"Key {gemini_key} is invalid"
        )

        assert "AIza" not in entry.session_id
        assert "AIza" not in entry.error_message
        assert "[REDACTED]" in entry.session_id
        assert "[REDACTED]" in entry.error_message

    def test_prompt_content_excluded_from_image_generation_log(self, audit_logger):
        """GIVEN image generation with prompt WHEN logged THEN prompt not in log."""
        sensitive_prompt = "Create an image about Python programming with API key sk-test123"

        entry = audit_logger.log_image_generation(
            session_id="prompt-test",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            request_metadata={
                "prompt": sensitive_prompt,
                "prompt_used": sensitive_prompt,
                "custom_prompt": sensitive_prompt,
                "safe_field": "visible"
            }
        )

        # Verify prompt content is excluded
        entry_dict = entry.to_dict()
        entry_json = entry.to_json()

        assert "Python programming" not in entry_json
        assert "sk-test123" not in entry_json
        assert "prompt" not in entry_dict.get("details", {})
        # Safe fields should still be present
        assert entry.details.get("safe_field") == "visible"

    def test_post_content_excluded_from_image_generation_log(self, audit_logger):
        """GIVEN image generation with post content WHEN logged THEN content not in log."""
        entry = audit_logger.log_image_generation(
            session_id="content-test",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            request_metadata={
                "post_content": "This is my LinkedIn post about machine learning",
                "content": "More content here",
                "text": "Some text",
                "dimensions": "should_be_overwritten"
            }
        )

        entry_json = entry.to_json()
        assert "LinkedIn post" not in entry_json
        assert "machine learning" not in entry_json
        assert "More content" not in entry_json
        assert "Some text" not in entry_json

    def test_details_dict_values_redacted(self, audit_logger):
        """GIVEN request details with sensitive keys WHEN logged THEN values redacted."""
        entry = audit_logger.log_key_connect(
            session_id="test-session",
            provider="openai",
            status=AuditStatus.SUCCESS,
            request_details={
                "api_key": "sk-secret123",
                "token": "bearer-token-123",
                "password": "supersecret",
                "user_id": "user-123"  # Should NOT be redacted
            }
        )

        assert entry.details is not None
        assert entry.details.get("api_key") == "[REDACTED]"
        assert entry.details.get("token") == "[REDACTED]"
        assert entry.details.get("password") == "[REDACTED]"
        assert entry.details.get("user_id") == "user-123"

    def test_unauthorized_access_redacts_api_keys_in_path(self, audit_logger):
        """GIVEN unauthorized access with API key in path WHEN logged THEN key redacted."""
        entry = audit_logger.log_unauthorized_access(
            session_id="unauth-session",
            request_path="/api/connect?key=sk-secretkey123",
            request_method="POST"
        )

        assert "sk-" not in entry.request_path
        assert "[REDACTED]" in entry.request_path

    def test_to_json_does_not_leak_sensitive_data(self, audit_logger):
        """GIVEN audit entry WHEN serialized to JSON THEN no sensitive data exposed."""
        entry = audit_logger.log_key_connect(
            session_id="json-test-sk-abc123",
            provider="openai",
            status=AuditStatus.FAILURE,
            error_message="Invalid key: sk-invalidkey123",
            request_details={"api_key": "sk-secret456", "region": "us-east"}
        )

        json_output = entry.to_json()

        # Parse and verify
        parsed = json.loads(json_output)
        assert "sk-" not in json_output
        assert parsed["details"]["api_key"] == "[REDACTED]"
        assert parsed["details"]["region"] == "us-east"


# =============================================================================
# AC4: Filtering by Date and Session
# =============================================================================

class TestAuditLogFiltering:
    """Tests for filtering audit logs by date and session."""

    def test_query_by_session(self, audit_logger):
        """GIVEN audit logs WHEN queried by session THEN returns matching entries."""
        audit_logger.log_key_connect("session-A", "gemini", AuditStatus.SUCCESS)
        audit_logger.log_key_connect("session-B", "openai", AuditStatus.SUCCESS)
        audit_logger.log_key_disconnect("session-A", "gemini")
        audit_logger.log_image_generation("session-A", AuditStatus.SUCCESS, "1200x627")

        results = audit_logger.query_by_session("session-A")

        assert len(results) == 3
        for entry in results:
            assert entry.session_id == "session-A"

    def test_query_by_session_returns_empty_for_unknown(self, audit_logger):
        """GIVEN audit logs WHEN queried by unknown session THEN returns empty list."""
        audit_logger.log_key_connect("session-X", "gemini", AuditStatus.SUCCESS)

        results = audit_logger.query_by_session("nonexistent-session")

        assert len(results) == 0

    def test_query_by_timestamp_range(self, audit_logger):
        """GIVEN audit logs WHEN queried by date range THEN returns matching entries."""
        # Create entries with controlled timestamps
        with patch.object(audit_logger, '_get_timestamp') as mock_ts:
            mock_ts.return_value = "2026-01-14T10:00:00Z"
            audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T12:00:00Z"
            audit_logger.log_key_connect("session-2", "openai", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T14:00:00Z"
            audit_logger.log_key_disconnect("session-3", "claude")

        # Query for middle time range
        results = audit_logger.query_by_timestamp_range(
            "2026-01-14T11:00:00Z",
            "2026-01-14T13:00:00Z"
        )

        assert len(results) == 1
        assert results[0].session_id == "session-2"

    def test_query_by_timestamp_range_inclusive(self, audit_logger):
        """GIVEN audit logs WHEN queried by date range THEN boundaries are inclusive."""
        with patch.object(audit_logger, '_get_timestamp') as mock_ts:
            mock_ts.return_value = "2026-01-14T10:00:00Z"
            audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T12:00:00Z"
            audit_logger.log_key_connect("session-2", "openai", AuditStatus.SUCCESS)

        results = audit_logger.query_by_timestamp_range(
            "2026-01-14T10:00:00Z",
            "2026-01-14T12:00:00Z"
        )

        assert len(results) == 2

    def test_query_by_session_and_timestamp(self, audit_logger):
        """GIVEN audit logs WHEN queried by session AND date THEN returns matching entries."""
        with patch.object(audit_logger, '_get_timestamp') as mock_ts:
            mock_ts.return_value = "2026-01-14T10:00:00Z"
            audit_logger.log_key_connect("session-A", "gemini", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T12:00:00Z"
            audit_logger.log_key_connect("session-A", "openai", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T12:00:00Z"
            audit_logger.log_key_connect("session-B", "claude", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T14:00:00Z"
            audit_logger.log_key_disconnect("session-A", "gemini")

        results = audit_logger.query_by_session_and_timestamp(
            "session-A",
            "2026-01-14T11:00:00Z",
            "2026-01-14T13:00:00Z"
        )

        assert len(results) == 1
        assert results[0].session_id == "session-A"
        assert results[0].provider == "openai"

    def test_query_by_event_type(self, audit_logger):
        """GIVEN audit logs WHEN queried by event type THEN returns matching entries."""
        audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)
        audit_logger.log_key_disconnect("session-1", "gemini")
        audit_logger.log_image_generation("session-1", AuditStatus.SUCCESS, "1200x627")
        audit_logger.log_image_generation("session-2", AuditStatus.FAILURE, "1080x1080")

        results = audit_logger.query_by_event_type(AuditEventType.IMAGE_GENERATION)

        assert len(results) == 2
        for entry in results:
            assert entry.event_type == AuditEventType.IMAGE_GENERATION

    def test_get_all_entries(self, audit_logger):
        """GIVEN audit logs WHEN get_all_entries called THEN returns all entries."""
        audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)
        audit_logger.log_key_disconnect("session-1", "gemini")
        audit_logger.log_image_generation("session-1", AuditStatus.SUCCESS, "1200x627")

        all_entries = audit_logger.get_all_entries()

        assert len(all_entries) == 3

    def test_clear_entries(self, audit_logger):
        """GIVEN audit logs WHEN clear_entries called THEN all entries removed."""
        audit_logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)
        audit_logger.log_key_disconnect("session-1", "gemini")

        audit_logger.clear_entries()

        assert len(audit_logger.get_all_entries()) == 0


# =============================================================================
# Audit Entry Serialization Tests
# =============================================================================

class TestAuditEntrySerialization:
    """Tests for AuditEntry serialization methods."""

    def test_to_dict_excludes_none_values(self):
        """GIVEN AuditEntry with None values WHEN to_dict THEN None values excluded."""
        entry = AuditEntry(
            event_type=AuditEventType.KEY_CONNECT,
            session_id="test-session",
            timestamp="2026-01-14T10:00:00Z",
            status=AuditStatus.SUCCESS,
            provider="gemini",
            # These are None
            details=None,
            error_message=None
        )

        result = entry.to_dict()

        assert "details" not in result
        assert "error_message" not in result
        assert result["event_type"] == "key_connect"
        assert result["status"] == "success"

    def test_to_dict_converts_enum_to_value(self):
        """GIVEN AuditEntry with enum values WHEN to_dict THEN enums converted to strings."""
        entry = AuditEntry(
            event_type=AuditEventType.IMAGE_GENERATION,
            session_id="test-session",
            timestamp="2026-01-14T10:00:00Z",
            status=AuditStatus.FAILURE
        )

        result = entry.to_dict()

        assert result["event_type"] == "image_generation"
        assert result["status"] == "failure"
        assert isinstance(result["event_type"], str)

    def test_to_json_returns_valid_json(self):
        """GIVEN AuditEntry WHEN to_json THEN returns valid JSON string."""
        entry = AuditEntry(
            event_type=AuditEventType.KEY_CONNECT,
            session_id="test-session",
            timestamp="2026-01-14T10:00:00Z",
            status=AuditStatus.SUCCESS,
            provider="gemini",
            details={"key": "value"}
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "key_connect"
        assert parsed["session_id"] == "test-session"
        assert parsed["details"]["key"] == "value"


# =============================================================================
# Global Audit Logger Tests
# =============================================================================

class TestGlobalAuditLogger:
    """Tests for global audit logger functions."""

    def test_get_audit_logger_returns_singleton(self, reset_global_logger):
        """GIVEN get_audit_logger WHEN called multiple times THEN returns same instance."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

    def test_reset_audit_logger_creates_new_instance(self, reset_global_logger):
        """GIVEN audit logger with entries WHEN reset THEN entries cleared."""
        logger = get_audit_logger()
        logger.log_key_connect("session-1", "gemini", AuditStatus.SUCCESS)

        reset_audit_logger()
        new_logger = get_audit_logger()

        assert len(new_logger.get_all_entries()) == 0


# =============================================================================
# Integration Tests with Routes
# =============================================================================

class TestAuditLoggingIntegration:
    """Integration tests for audit logging with API routes."""

    def test_gemini_connect_creates_audit_log(self, reset_global_logger):
        """GIVEN Gemini connect route WHEN called THEN audit log created."""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, AsyncMock

        # Import after reset to get fresh logger
        from src.api.gemini_routes import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch('src.api.gemini_routes.validate_gemini_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/auth/gemini/connect",
                json={"api_key": "AIzaSyC123456789abcdefghijklmnopqrstuvwxy"},
                headers={"X-Session-ID": "integration-test-session"}
            )

            assert response.status_code == 200

            # Check audit log was created
            logger = get_audit_logger()
            entries = logger.query_by_session("integration-test-session")

            assert len(entries) >= 1
            connect_entry = next(
                (e for e in entries if e.event_type == AuditEventType.KEY_CONNECT),
                None
            )
            assert connect_entry is not None
            assert connect_entry.provider == "gemini"
            assert connect_entry.status == AuditStatus.SUCCESS

    def test_gemini_disconnect_creates_audit_log(self, reset_global_logger):
        """GIVEN Gemini disconnect route WHEN called THEN audit log created."""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, MagicMock

        from src.api.gemini_routes import router, get_gemini_key_storage
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Pre-populate key storage
        storage = get_gemini_key_storage()
        storage.store("disconnect-test-session", "AIzaSyC123456789abcdefghijklmnopqrstuvwxy")

        response = client.post(
            "/auth/gemini/disconnect",
            headers={"X-Session-ID": "disconnect-test-session"}
        )

        assert response.status_code == 200

        # Check audit log was created
        logger = get_audit_logger()
        entries = logger.query_by_session("disconnect-test-session")

        disconnect_entry = next(
            (e for e in entries if e.event_type == AuditEventType.KEY_DISCONNECT),
            None
        )
        assert disconnect_entry is not None
        assert disconnect_entry.provider == "gemini"
        assert disconnect_entry.status == AuditStatus.SUCCESS

    def test_image_generation_creates_audit_log(self, reset_global_logger):
        """GIVEN image generation route WHEN called THEN audit log created."""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, AsyncMock, MagicMock

        from src.api.image_routes import router
        from src.api.gemini_routes import get_gemini_key_storage
        from src.services.gemini_client import ImageGenerationResult
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Set up Gemini key
        storage = get_gemini_key_storage()
        storage.store("image-gen-session", "AIzaSyC123456789abcdefghijklmnopqrstuvwxy")

        # Mock GeminiClient.generate_image
        mock_result = ImageGenerationResult(
            success=True,
            image_base64="base64encodedimage",
            error=None
        )

        with patch('src.api.image_routes.GeminiClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.generate_image = AsyncMock(return_value=mock_result)
            MockClient.return_value = mock_client_instance

            response = client.post(
                "/generate/image",
                json={
                    "post_content": "Test post about Python",
                    "dimensions": "1200x627"
                },
                headers={"X-Session-ID": "image-gen-session"}
            )

            assert response.status_code == 200

            # Check audit log was created
            logger = get_audit_logger()
            entries = logger.query_by_session("image-gen-session")

            img_entry = next(
                (e for e in entries if e.event_type == AuditEventType.IMAGE_GENERATION),
                None
            )
            assert img_entry is not None
            assert img_entry.status == AuditStatus.SUCCESS
            assert img_entry.details.get("dimensions") == "1200x627"
            # Verify prompt content is NOT in the audit log
            assert "Python" not in img_entry.to_json()


# =============================================================================
# Acceptance Criteria Summary Tests
# =============================================================================

class TestAcceptanceCriteria:
    """Direct tests for each acceptance criterion."""

    def test_ac1_key_connect_creates_audit_with_timestamp_and_session(self, audit_logger):
        """AC1: GIVEN API key connect/disconnect WHEN action completes THEN audit log
        created with timestamp and session ID."""
        entry = audit_logger.log_key_connect(
            session_id="ac1-test-session",
            provider="gemini",
            status=AuditStatus.SUCCESS
        )

        assert entry.timestamp is not None
        assert entry.session_id == "ac1-test-session"
        assert entry.timestamp.endswith("Z")  # UTC timestamp

    def test_ac2_image_generation_creates_audit_with_metadata(self, audit_logger):
        """AC2: GIVEN image generation WHEN completed THEN audit log created with
        request metadata."""
        entry = audit_logger.log_image_generation(
            session_id="ac2-test-session",
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            style="minimalist",
            content_type="TUTORIAL",
            request_metadata={"request_id": "req-123"}
        )

        assert entry.details is not None
        assert entry.details["dimensions"] == "1200x627"
        assert entry.details["style"] == "minimalist"
        assert entry.details["content_type"] == "TUTORIAL"
        assert entry.details["request_id"] == "req-123"

    def test_ac3_audit_log_contains_no_sensitive_data(self, audit_logger):
        """AC3: GIVEN any audit log WHEN written THEN contains no sensitive data
        (API keys, prompt content)."""
        # Test with various sensitive data
        entry = audit_logger.log_image_generation(
            session_id="ac3-sk-secretkey123",  # API key in session
            status=AuditStatus.SUCCESS,
            dimensions="1200x627",
            error_message="Error with key sk-anotherkey456",  # API key in error
            request_metadata={
                "prompt": "This is the prompt content",  # Should be excluded
                "api_key": "sk-secret789",  # Should be redacted
                "safe_data": "visible"
            }
        )

        json_output = entry.to_json()

        # Verify no sensitive data
        assert "sk-" not in json_output
        assert "prompt content" not in json_output
        assert "[REDACTED]" in json_output or "sk-" not in entry.session_id
        assert "visible" in json_output  # Safe data should be present

    def test_ac4_audit_logs_support_filtering_by_date_and_session(self, audit_logger):
        """AC4: GIVEN audit logs WHEN queried THEN support filtering by date and session."""
        with patch.object(audit_logger, '_get_timestamp') as mock_ts:
            mock_ts.return_value = "2026-01-14T10:00:00Z"
            audit_logger.log_key_connect("session-A", "gemini", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T12:00:00Z"
            audit_logger.log_key_connect("session-B", "openai", AuditStatus.SUCCESS)

            mock_ts.return_value = "2026-01-14T14:00:00Z"
            audit_logger.log_image_generation("session-A", AuditStatus.SUCCESS, "1200x627")

        # Filter by session
        session_results = audit_logger.query_by_session("session-A")
        assert len(session_results) == 2

        # Filter by timestamp
        time_results = audit_logger.query_by_timestamp_range(
            "2026-01-14T11:00:00Z",
            "2026-01-14T13:00:00Z"
        )
        assert len(time_results) == 1

        # Filter by both
        combined_results = audit_logger.query_by_session_and_timestamp(
            "session-A",
            "2026-01-14T09:00:00Z",
            "2026-01-14T11:00:00Z"
        )
        assert len(combined_results) == 1
