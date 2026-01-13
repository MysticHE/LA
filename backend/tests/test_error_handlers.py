"""Tests for secure error handling.

Tests verify that:
1. 500 errors return generic messages only
2. API keys, path traces, and internal details are never exposed
3. OpenAI API errors are safely sanitized
4. Error handling passes security review for information disclosure
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.api.error_handlers import (
    sanitize_error_message,
    is_safe_error_detail,
    create_safe_error_response,
    register_error_handlers,
    sanitize_openai_error,
    sanitize_anthropic_error,
)


# ============================================================
# Test sanitize_error_message
# ============================================================

class TestSanitizeErrorMessage:
    """Tests for the sanitize_error_message function."""

    def test_sanitize_empty_message(self):
        """Test that empty messages are returned unchanged."""
        assert sanitize_error_message("") == ""
        assert sanitize_error_message(None) is None

    def test_sanitize_safe_message(self):
        """Test that safe messages are not altered."""
        safe_messages = [
            "Invalid API key",
            "Rate limit exceeded",
            "Connection failed",
            "Request timed out",
            "Bad request: missing required field",
        ]
        for msg in safe_messages:
            assert sanitize_error_message(msg) == msg

    def test_sanitize_openai_api_key(self):
        """Test that OpenAI API keys are redacted."""
        message = "Error with key sk-1234567890abcdefghijklmnopqrstuvwxyz1234"
        result = sanitize_error_message(message)
        assert "sk-" not in result
        assert "[REDACTED]" in result

    def test_sanitize_anthropic_api_key(self):
        """Test that Anthropic API keys are redacted."""
        message = "Error with key sk-ant-api03-abcdefghij1234567890-ABCDEFGHIJ1234567890"
        result = sanitize_error_message(message)
        assert "sk-ant-" not in result
        assert "[REDACTED]" in result

    def test_sanitize_windows_path(self):
        """Test that Windows file paths are redacted."""
        message = "Error at C:\\Users\\john\\project\\secrets.py"
        result = sanitize_error_message(message)
        assert "C:\\" not in result
        assert "[REDACTED]" in result

    def test_sanitize_unix_path_home(self):
        """Test that Unix home paths are redacted."""
        message = "Error at /home/user/project/config.py"
        result = sanitize_error_message(message)
        assert "/home/" not in result
        assert "[REDACTED]" in result

    def test_sanitize_unix_path_users(self):
        """Test that macOS Users paths are redacted."""
        message = "Error at /Users/developer/code/app.py"
        result = sanitize_error_message(message)
        assert "/Users/" not in result
        assert "[REDACTED]" in result

    def test_sanitize_stack_trace_file_line(self):
        """Test that stack trace file references are redacted."""
        message = 'File "/home/user/app.py", line 42, in main'
        result = sanitize_error_message(message)
        assert 'File "' not in result
        assert "[REDACTED]" in result

    def test_sanitize_traceback_header(self):
        """Test that traceback headers are redacted."""
        message = "Traceback (most recent call last):\n  File..."
        result = sanitize_error_message(message)
        assert "Traceback (most recent call last)" not in result
        assert "[REDACTED]" in result

    def test_sanitize_site_packages_path(self):
        """Test that site-packages paths are redacted."""
        message = "Error in site-packages/requests/api.py:75"
        result = sanitize_error_message(message)
        assert "site-packages" not in result
        assert "[REDACTED]" in result

    def test_sanitize_multiple_sensitive_items(self):
        """Test that multiple sensitive items are all redacted."""
        message = (
            "Error: key sk-abc123456789012345678901234567890123 "
            "at /home/user/app.py"
        )
        result = sanitize_error_message(message)
        assert "sk-" not in result
        assert "/home/" not in result
        assert result.count("[REDACTED]") == 2


# ============================================================
# Test is_safe_error_detail
# ============================================================

class TestIsSafeErrorDetail:
    """Tests for the is_safe_error_detail function."""

    def test_none_is_safe(self):
        """Test that None is considered safe."""
        assert is_safe_error_detail(None) is True

    def test_safe_string_is_safe(self):
        """Test that safe strings are identified as safe."""
        assert is_safe_error_detail("Invalid request") is True
        assert is_safe_error_detail("Rate limit exceeded") is True

    def test_api_key_is_not_safe(self):
        """Test that API keys are identified as unsafe."""
        assert is_safe_error_detail("Key: sk-abc123456789012345678901234") is False

    def test_path_is_not_safe(self):
        """Test that file paths are identified as unsafe."""
        assert is_safe_error_detail("/home/user/secret.py") is False
        assert is_safe_error_detail("C:\\Users\\admin\\config.ini") is False


# ============================================================
# Test create_safe_error_response
# ============================================================

class TestCreateSafeErrorResponse:
    """Tests for the create_safe_error_response function."""

    def test_500_returns_generic_message(self):
        """Test that 500 errors return generic messages regardless of detail."""
        response = create_safe_error_response(
            status_code=500,
            detail="Detailed internal error with sk-secret123456789012345678"
        )
        assert "sk-" not in response["detail"]
        assert "internal" not in response["detail"].lower() or "internal server error" in response["detail"].lower()
        assert response["detail"] == "An internal server error occurred. Please try again later."

    def test_502_returns_generic_message(self):
        """Test that 502 errors return generic messages."""
        response = create_safe_error_response(status_code=502, detail="Upstream error")
        assert response["detail"] == "Bad gateway. Please try again later."

    def test_503_returns_generic_message(self):
        """Test that 503 errors return generic messages."""
        response = create_safe_error_response(status_code=503, detail="Service down")
        assert response["detail"] == "Service temporarily unavailable. Please try again later."

    def test_504_returns_generic_message(self):
        """Test that 504 errors return generic messages."""
        response = create_safe_error_response(status_code=504, detail="Timeout")
        assert response["detail"] == "Gateway timeout. Please try again later."

    def test_400_with_safe_detail(self):
        """Test that 400 errors pass through safe details."""
        response = create_safe_error_response(
            status_code=400,
            detail="Invalid email format"
        )
        assert response["detail"] == "Invalid email format"

    def test_400_with_unsafe_detail(self):
        """Test that 400 errors sanitize unsafe details."""
        response = create_safe_error_response(
            status_code=400,
            detail="Error with key sk-abc123456789012345678901234",
            default_message="An error occurred."
        )
        assert "sk-" not in response["detail"]
        assert response["detail"] == "An error occurred."

    def test_401_with_safe_detail(self):
        """Test that 401 errors pass through safe details."""
        response = create_safe_error_response(
            status_code=401,
            detail="Authentication required"
        )
        assert response["detail"] == "Authentication required"


# ============================================================
# Test sanitize_openai_error
# ============================================================

class TestSanitizeOpenAIError:
    """Tests for the sanitize_openai_error function."""

    def test_authentication_error(self):
        """Test that authentication errors are mapped correctly."""
        result = sanitize_openai_error("authentication error: invalid api key")
        assert result == "Invalid API key. Please reconnect with a valid OpenAI API key."

    def test_invalid_api_key_error(self):
        """Test that invalid api key errors are mapped correctly."""
        result = sanitize_openai_error("Invalid API key provided")
        assert result == "Invalid API key. Please reconnect with a valid OpenAI API key."

    def test_rate_limit_error(self):
        """Test that rate limit errors are mapped correctly."""
        result = sanitize_openai_error("Rate limit exceeded for model gpt-4")
        assert result == "Rate limit exceeded. Please try again later."

    def test_quota_error(self):
        """Test that quota errors are mapped correctly."""
        result = sanitize_openai_error("You exceeded your current quota")
        assert result == "API quota exceeded. Please check your OpenAI billing settings."

    def test_billing_error(self):
        """Test that billing errors are mapped correctly."""
        result = sanitize_openai_error("Billing hard limit reached")
        assert result == "API quota exceeded. Please check your OpenAI billing settings."

    def test_permission_error(self):
        """Test that permission errors are mapped correctly."""
        result = sanitize_openai_error("You don't have permission to use this model")
        assert result == "API key does not have permission to perform this action."

    def test_connection_error(self):
        """Test that connection errors are mapped correctly."""
        result = sanitize_openai_error("Connection error: failed to reach API")
        assert result == "Could not connect to OpenAI API. Please check your network connection."

    def test_unknown_error(self):
        """Test that unknown errors return generic message."""
        result = sanitize_openai_error("Some random internal error occurred")
        assert result == "Failed to process request. Please try again."

    def test_empty_error(self):
        """Test that empty errors return generic message."""
        result = sanitize_openai_error("")
        assert result == "Failed to process request. Please try again."


# ============================================================
# Test sanitize_anthropic_error
# ============================================================

class TestSanitizeAnthropicError:
    """Tests for the sanitize_anthropic_error function."""

    def test_authentication_error(self):
        """Test that authentication errors are mapped correctly."""
        result = sanitize_anthropic_error("authentication error: invalid key")
        assert result == "Invalid API key. Please reconnect with a valid Claude API key."

    def test_rate_limit_error(self):
        """Test that rate limit errors are mapped correctly."""
        result = sanitize_anthropic_error("Rate limit exceeded for API")
        assert result == "Rate limit exceeded. Please try again later."

    def test_permission_error(self):
        """Test that permission errors are mapped correctly."""
        result = sanitize_anthropic_error("Permission denied for this operation")
        assert result == "API key does not have permission to perform this action."

    def test_connection_error(self):
        """Test that connection errors are mapped correctly."""
        result = sanitize_anthropic_error("Connection error to Anthropic")
        assert result == "Could not connect to Claude API. Please check your network connection."

    def test_unknown_error(self):
        """Test that unknown errors return generic message."""
        result = sanitize_anthropic_error("Internal processing error")
        assert result == "Failed to process request. Please try again."


# ============================================================
# Test Error Handler Integration
# ============================================================

class TestErrorHandlerIntegration:
    """Integration tests for error handlers with FastAPI."""

    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI app with error handlers."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/raise-500")
        async def raise_500():
            raise Exception("Internal error with sk-secret123456789012345678901234")

        @app.get("/raise-http-500")
        async def raise_http_500():
            raise HTTPException(
                status_code=500,
                detail="Database error at /home/user/db.py"
            )

        @app.get("/raise-400")
        async def raise_400():
            raise HTTPException(status_code=400, detail="Invalid email format")

        @app.get("/raise-401")
        async def raise_401():
            raise HTTPException(status_code=401, detail="Not authenticated")

        @app.get("/raise-404")
        async def raise_404():
            raise HTTPException(status_code=404, detail="Resource not found")

        @app.get("/raise-429")
        async def raise_429():
            raise HTTPException(
                status_code=429,
                detail="Rate limited",
                headers={"Retry-After": "60"}
            )

        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app, raise_server_exceptions=False)

    def test_unhandled_exception_returns_generic_500(self, client):
        """Test that unhandled exceptions return generic 500 message."""
        response = client.get("/raise-500")
        assert response.status_code == 500
        body = response.json()
        # Should not contain API key
        assert "sk-" not in body["detail"]
        # Should be generic message
        assert body["detail"] == "An internal server error occurred. Please try again later."

    def test_http_500_returns_generic_message(self, client):
        """Test that HTTP 500 returns generic message, not detail."""
        response = client.get("/raise-http-500")
        assert response.status_code == 500
        body = response.json()
        # Should not contain path
        assert "/home/" not in body["detail"]
        # Should be generic message
        assert body["detail"] == "An internal server error occurred. Please try again later."

    def test_http_400_passes_safe_detail(self, client):
        """Test that HTTP 400 passes through safe detail."""
        response = client.get("/raise-400")
        assert response.status_code == 400
        body = response.json()
        assert body["detail"] == "Invalid email format"

    def test_http_401_passes_safe_detail(self, client):
        """Test that HTTP 401 passes through safe detail."""
        response = client.get("/raise-401")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"] == "Not authenticated"

    def test_http_404_passes_safe_detail(self, client):
        """Test that HTTP 404 passes through safe detail."""
        response = client.get("/raise-404")
        assert response.status_code == 404
        body = response.json()
        assert body["detail"] == "Resource not found"

    def test_http_429_preserves_retry_after_header(self, client):
        """Test that HTTP 429 preserves Retry-After header."""
        response = client.get("/raise-429")
        assert response.status_code == 429
        body = response.json()
        assert body["detail"] == "Rate limited"
        assert response.headers.get("Retry-After") == "60"


# ============================================================
# Security Review Tests
# ============================================================

class TestSecurityReview:
    """Security-focused tests for error handling."""

    def test_no_api_key_in_500_errors(self):
        """SECURITY: 500 errors must never contain API keys."""
        test_cases = [
            "Error with sk-1234567890123456789012345678901234567890",
            "Key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz-1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        ]
        for detail in test_cases:
            response = create_safe_error_response(status_code=500, detail=detail)
            assert "sk-" not in response["detail"], f"API key leaked in response for: {detail}"

    def test_no_path_traces_in_500_errors(self):
        """SECURITY: 500 errors must never contain file paths."""
        test_cases = [
            "Error at /home/user/app.py:42",
            "File C:\\Users\\admin\\secrets.json not found",
            "Exception in /var/www/app/config.py",
        ]
        for detail in test_cases:
            response = create_safe_error_response(status_code=500, detail=detail)
            assert "/home/" not in response["detail"]
            assert "/var/" not in response["detail"]
            assert "C:\\" not in response["detail"]
            assert "/Users/" not in response["detail"]

    def test_no_stack_traces_in_500_errors(self):
        """SECURITY: 500 errors must never contain stack traces."""
        detail = """Traceback (most recent call last):
  File "/home/user/app.py", line 42, in main
    raise ValueError("test")
ValueError: test"""
        response = create_safe_error_response(status_code=500, detail=detail)
        assert "Traceback" not in response["detail"]
        assert "File " not in response["detail"]
        assert "line " not in response["detail"]

    def test_no_internal_details_in_client_errors(self):
        """SECURITY: Client errors must not expose internal details."""
        test_cases = [
            ("Error with key sk-1234567890123456789012345678901234567890", "An error occurred."),
            ("Database error at /var/lib/postgresql/data", "An error occurred."),
        ]
        for detail, default in test_cases:
            response = create_safe_error_response(
                status_code=400,
                detail=detail,
                default_message=default
            )
            assert "sk-" not in response["detail"]
            assert "/var/" not in response["detail"]

    def test_safe_openai_error_properties(self):
        """SECURITY: Only safe OpenAI error properties are passed through."""
        # Simulate raw OpenAI error messages that might contain sensitive info
        raw_errors = [
            "Error code: 401 - {'error': {'message': 'Invalid API key', 'type': 'invalid_api_key', 'param': None, 'code': 'invalid_api_key'}}",
            "Request failed with api key sk-test123456789012345678901234567890",
            "Connection to api.openai.com failed at /home/user/openai-python/src/client.py",
        ]
        for raw_error in raw_errors:
            safe_msg = sanitize_openai_error(raw_error)
            assert "sk-" not in safe_msg
            assert "/home/" not in safe_msg
            assert "param" not in safe_msg
            assert "code" not in safe_msg.lower() or safe_msg.startswith("Could not connect")

    def test_consistent_generic_messages_for_server_errors(self):
        """SECURITY: All 5xx errors return consistent generic messages."""
        expected_messages = {
            500: "An internal server error occurred. Please try again later.",
            502: "Bad gateway. Please try again later.",
            503: "Service temporarily unavailable. Please try again later.",
            504: "Gateway timeout. Please try again later.",
        }
        for status_code, expected_msg in expected_messages.items():
            response = create_safe_error_response(
                status_code=status_code,
                detail="Sensitive internal error with paths and keys"
            )
            assert response["detail"] == expected_msg
