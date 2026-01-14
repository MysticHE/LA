"""Tests for secure error handling - US-SEC-005.

Tests verify the following acceptance criteria:
1. GIVEN any API error WHEN response generated THEN no stack traces in response body
2. GIVEN Gemini API error WHEN occurring THEN no API key in error message
3. GIVEN internal error WHEN occurring THEN return generic 500 message with correlation ID
4. GIVEN validation error WHEN occurring THEN return helpful message without internal paths

Security compliance: OWASP A02 and A09
"""

import pytest
import re
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from src.api.error_handlers import (
    sanitize_error_message,
    is_safe_error_detail,
    create_safe_error_response,
    register_error_handlers,
    sanitize_gemini_error,
    generate_correlation_id,
)


# ============================================================
# Acceptance Criteria 1: No stack traces in response body
# ============================================================

class TestNoStackTracesInResponse:
    """AC1: GIVEN any API error WHEN response generated THEN no stack traces in response body."""

    def test_stack_trace_removed_from_error_message(self):
        """Stack traces should be redacted from error messages."""
        stack_trace = """Traceback (most recent call last):
  File "/home/user/app.py", line 42, in main
    raise ValueError("test")
ValueError: test"""

        result = sanitize_error_message(stack_trace)
        assert "Traceback" not in result
        assert 'File "' not in result
        assert "line 42" not in result
        assert "[REDACTED]" in result

    def test_file_line_reference_removed(self):
        """File:line references should be redacted."""
        error = 'Error at File "/var/www/app.py", line 100, in handler'
        result = sanitize_error_message(error)
        assert "/var/www" not in result
        assert "line 100" not in result

    def test_500_error_never_contains_stack_trace(self):
        """500 errors should never expose stack traces regardless of input."""
        detail_with_trace = """Internal error:
Traceback (most recent call last):
  File "/home/user/services/api.py", line 42
    return process_request()
RuntimeError: Database connection failed"""

        response = create_safe_error_response(status_code=500, detail=detail_with_trace)
        assert "Traceback" not in response["detail"]
        assert "File " not in response["detail"]
        assert "RuntimeError" not in response["detail"]
        assert response["detail"] == "An internal server error occurred. Please try again later."

    @pytest.fixture
    def test_app_with_handlers(self):
        """Create a test FastAPI app with error handlers."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/raise-exception-with-trace")
        async def raise_exception():
            raise Exception(
                """Traceback (most recent call last):
  File "/home/user/app.py", line 42
ValueError: test error"""
            )

        @app.get("/raise-http-500-with-trace")
        async def raise_http_500():
            raise HTTPException(
                status_code=500,
                detail='File "/var/lib/app.py", line 100 failed'
            )

        return app

    def test_unhandled_exception_no_stack_trace(self, test_app_with_handlers):
        """Unhandled exceptions should not expose stack traces."""
        client = TestClient(test_app_with_handlers, raise_server_exceptions=False)
        response = client.get("/raise-exception-with-trace")
        assert response.status_code == 500
        body = response.json()
        assert "Traceback" not in body["detail"]
        assert "File " not in body["detail"]
        assert "line " not in body["detail"]

    def test_http_500_no_stack_trace(self, test_app_with_handlers):
        """HTTP 500 errors should not expose stack traces."""
        client = TestClient(test_app_with_handlers, raise_server_exceptions=False)
        response = client.get("/raise-http-500-with-trace")
        assert response.status_code == 500
        body = response.json()
        assert "File " not in body["detail"]
        assert "/var/lib" not in body["detail"]


# ============================================================
# Acceptance Criteria 2: No API key in Gemini error message
# ============================================================

class TestNoGeminiApiKeyInErrors:
    """AC2: GIVEN Gemini API error WHEN occurring THEN no API key in error message."""

    def test_gemini_api_key_redacted_from_message(self):
        """Gemini API keys (AIza...) should be redacted from error messages."""
        error_with_key = "Error with key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz"
        result = sanitize_error_message(error_with_key)
        assert "AIza" not in result
        assert "[REDACTED]" in result

    def test_sanitize_gemini_error_removes_api_key(self):
        """sanitize_gemini_error should remove API keys from messages."""
        error_with_key = "Authentication failed for key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz"
        result = sanitize_gemini_error(error_with_key)
        assert "AIza" not in result
        assert result == "Failed to process request. Please try again."

    def test_sanitize_gemini_error_authentication(self):
        """Gemini authentication errors should be sanitized."""
        result = sanitize_gemini_error("Invalid API key provided")
        assert result == "Invalid API key. Please reconnect with a valid Gemini API key."

    def test_sanitize_gemini_error_401(self):
        """Gemini 401 errors should be sanitized."""
        result = sanitize_gemini_error("Error code: 401 - unauthorized")
        assert result == "Invalid API key. Please reconnect with a valid Gemini API key."

    def test_sanitize_gemini_error_rate_limit(self):
        """Gemini rate limit errors should be sanitized."""
        result = sanitize_gemini_error("Rate limit exceeded for API")
        assert result == "Rate limit exceeded. Please try again later."

    def test_sanitize_gemini_error_429(self):
        """Gemini 429 errors should be sanitized."""
        result = sanitize_gemini_error("Error code: 429 - too many requests")
        assert result == "Rate limit exceeded. Please try again later."

    def test_sanitize_gemini_error_quota(self):
        """Gemini quota errors should be sanitized."""
        result = sanitize_gemini_error("Quota exceeded for project")
        assert result == "API quota exceeded. Please check your Gemini API billing settings."

    def test_sanitize_gemini_error_permission(self):
        """Gemini permission errors should be sanitized."""
        result = sanitize_gemini_error("Permission denied for resource")
        assert result == "API key does not have permission to perform this action."

    def test_sanitize_gemini_error_403(self):
        """Gemini 403 errors should be sanitized."""
        result = sanitize_gemini_error("Error code: 403 - forbidden")
        assert result == "API key does not have permission to perform this action."

    def test_sanitize_gemini_error_connection(self):
        """Gemini connection errors should be sanitized."""
        result = sanitize_gemini_error("Connection error to API")
        assert result == "Could not connect to Gemini API. Please check your network connection."

    def test_sanitize_gemini_error_400(self):
        """Gemini 400 errors should be sanitized."""
        result = sanitize_gemini_error("Error code: 400 - bad request")
        assert result == "Invalid request to Gemini API. Please try again."

    def test_sanitize_gemini_error_unknown(self):
        """Unknown Gemini errors should return generic message."""
        result = sanitize_gemini_error("Some internal processing error")
        assert result == "Failed to process request. Please try again."

    def test_sanitize_gemini_error_empty(self):
        """Empty error messages should return generic message."""
        result = sanitize_gemini_error("")
        assert result == "Failed to process request. Please try again."

    def test_gemini_api_key_pattern_detected(self):
        """Gemini API key patterns should be detected as unsafe."""
        assert is_safe_error_detail("Key: AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz") is False

    def test_create_safe_error_response_redacts_gemini_key(self):
        """create_safe_error_response should redact Gemini API keys."""
        response = create_safe_error_response(
            status_code=400,
            detail="Error with key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz",
            default_message="An error occurred."
        )
        assert "AIza" not in response["detail"]
        assert response["detail"] == "An error occurred."


# ============================================================
# Acceptance Criteria 3: Generic 500 with correlation ID
# ============================================================

class TestGeneric500WithCorrelationId:
    """AC3: GIVEN internal error WHEN occurring THEN return generic 500 message with correlation ID."""

    def test_generate_correlation_id_format(self):
        """Correlation IDs should be valid UUIDs."""
        correlation_id = generate_correlation_id()
        # Should be a valid UUID format
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', correlation_id)

    def test_generate_correlation_id_unique(self):
        """Each correlation ID should be unique."""
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_500_response_includes_correlation_id(self):
        """500 errors should include a correlation ID."""
        response = create_safe_error_response(status_code=500, detail="Internal error")
        assert "correlation_id" in response
        assert response["correlation_id"] is not None
        # Should be UUID format
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-', response["correlation_id"])

    def test_500_response_has_generic_message(self):
        """500 errors should have a generic message regardless of detail."""
        sensitive_detail = "Database connection failed at /home/user/db.py with password=secret"
        response = create_safe_error_response(status_code=500, detail=sensitive_detail)
        assert response["detail"] == "An internal server error occurred. Please try again later."
        assert "password" not in response["detail"]
        assert "/home/" not in response["detail"]

    def test_502_response_includes_correlation_id(self):
        """502 errors should include a correlation ID."""
        response = create_safe_error_response(status_code=502, detail="Upstream error")
        assert "correlation_id" in response
        assert response["detail"] == "Bad gateway. Please try again later."

    def test_503_response_includes_correlation_id(self):
        """503 errors should include a correlation ID."""
        response = create_safe_error_response(status_code=503, detail="Service down")
        assert "correlation_id" in response
        assert response["detail"] == "Service temporarily unavailable. Please try again later."

    def test_504_response_includes_correlation_id(self):
        """504 errors should include a correlation ID."""
        response = create_safe_error_response(status_code=504, detail="Timeout")
        assert "correlation_id" in response
        assert response["detail"] == "Gateway timeout. Please try again later."

    def test_provided_correlation_id_used(self):
        """When a correlation ID is provided, it should be used."""
        custom_id = "custom-correlation-id-12345"
        response = create_safe_error_response(
            status_code=500,
            detail="Error",
            correlation_id=custom_id
        )
        assert response["correlation_id"] == custom_id

    @pytest.fixture
    def test_app_with_handlers(self):
        """Create a test FastAPI app with error handlers."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/raise-internal-error")
        async def raise_internal_error():
            raise Exception("Internal database error with sensitive info")

        @app.get("/raise-http-500")
        async def raise_http_500():
            raise HTTPException(status_code=500, detail="Sensitive internal details")

        return app

    def test_unhandled_exception_has_correlation_id(self, test_app_with_handlers):
        """Unhandled exceptions should return correlation ID."""
        client = TestClient(test_app_with_handlers, raise_server_exceptions=False)
        response = client.get("/raise-internal-error")
        assert response.status_code == 500
        body = response.json()
        assert "correlation_id" in body
        assert body["detail"] == "An internal server error occurred. Please try again later."

    def test_http_500_has_correlation_id(self, test_app_with_handlers):
        """HTTP 500 errors should return correlation ID."""
        client = TestClient(test_app_with_handlers, raise_server_exceptions=False)
        response = client.get("/raise-http-500")
        assert response.status_code == 500
        body = response.json()
        assert "correlation_id" in body
        assert body["detail"] == "An internal server error occurred. Please try again later."


# ============================================================
# Acceptance Criteria 4: Validation errors without internal paths
# ============================================================

class TestValidationErrorsWithoutPaths:
    """AC4: GIVEN validation error WHEN occurring THEN return helpful message without internal paths."""

    def test_windows_path_redacted(self):
        """Windows file paths should be redacted."""
        error = r"Error loading config from C:\Users\admin\config.json"
        result = sanitize_error_message(error)
        assert "C:\\" not in result
        assert "[REDACTED]" in result

    def test_unix_home_path_redacted(self):
        """Unix /home paths should be redacted."""
        error = "Error loading module from /home/user/project/module.py"
        result = sanitize_error_message(error)
        assert "/home/" not in result
        assert "[REDACTED]" in result

    def test_unix_users_path_redacted(self):
        """macOS /Users paths should be redacted."""
        error = "Error in /Users/developer/code/app.py"
        result = sanitize_error_message(error)
        assert "/Users/" not in result
        assert "[REDACTED]" in result

    def test_var_path_redacted(self):
        """Unix /var paths should be redacted."""
        error = "Database error at /var/lib/postgresql/data"
        result = sanitize_error_message(error)
        assert "/var/" not in result
        assert "[REDACTED]" in result

    def test_tmp_path_redacted(self):
        """Unix /tmp paths should be redacted."""
        error = "Temp file at /tmp/upload_12345.dat"
        result = sanitize_error_message(error)
        assert "/tmp/" not in result
        assert "[REDACTED]" in result

    def test_etc_path_redacted(self):
        """Unix /etc paths should be redacted."""
        error = "Config error in /etc/myapp/settings.conf"
        result = sanitize_error_message(error)
        assert "/etc/" not in result
        assert "[REDACTED]" in result

    def test_site_packages_path_redacted(self):
        """Python site-packages paths should be redacted."""
        error = "Error in site-packages/requests/api.py"
        result = sanitize_error_message(error)
        assert "site-packages" not in result
        assert "[REDACTED]" in result

    def test_dist_packages_path_redacted(self):
        """Python dist-packages paths should be redacted."""
        error = "Error in dist-packages/flask/app.py"
        result = sanitize_error_message(error)
        assert "dist-packages" not in result
        assert "[REDACTED]" in result

    def test_safe_validation_message_preserved(self):
        """Safe validation messages should be preserved."""
        safe_messages = [
            "Invalid email format",
            "Field 'username' is required",
            "Value must be between 1 and 100",
            "Password must be at least 8 characters",
        ]
        for msg in safe_messages:
            result = sanitize_error_message(msg)
            assert result == msg  # Should be unchanged

    def test_400_error_with_path_sanitized(self):
        """400 errors with paths should be sanitized."""
        response = create_safe_error_response(
            status_code=400,
            detail="Error loading /home/user/config.json",
            default_message="Invalid configuration."
        )
        assert "/home/" not in response["detail"]
        assert response["detail"] == "Invalid configuration."

    def test_400_error_safe_detail_preserved(self):
        """400 errors with safe details should pass through."""
        response = create_safe_error_response(
            status_code=400,
            detail="Invalid email format"
        )
        assert response["detail"] == "Invalid email format"

    @pytest.fixture
    def test_app_with_validation(self):
        """Create a test FastAPI app with validation."""
        app = FastAPI()
        register_error_handlers(app)

        class TestModel(BaseModel):
            email: str

            @field_validator("email")
            @classmethod
            def validate_email(cls, v):
                if "@" not in v:
                    raise ValueError("Invalid email format")
                return v

        @app.post("/validate")
        async def validate_input(data: TestModel):
            return {"email": data.email}

        return app

    def test_pydantic_validation_error_no_paths(self, test_app_with_validation):
        """Pydantic validation errors should not expose internal paths."""
        client = TestClient(test_app_with_validation)
        response = client.post("/validate", json={"email": "invalid"})
        assert response.status_code == 422
        body = response.json()
        # Should have validation error structure
        assert "detail" in body
        assert "errors" in body
        # Should not contain any paths
        body_str = str(body)
        assert "/home/" not in body_str
        assert "site-packages" not in body_str


# ============================================================
# Security Review Tests
# ============================================================

class TestSecurityReview:
    """Comprehensive security tests for error handling."""

    def test_no_openai_api_key_exposure(self):
        """OpenAI API keys should never be exposed."""
        error = "Error with key sk-1234567890abcdefghijklmnopqrstuvwxyz1234"
        response = create_safe_error_response(status_code=500, detail=error)
        assert "sk-" not in response["detail"]

    def test_no_anthropic_api_key_exposure(self):
        """Anthropic API keys should never be exposed."""
        error = "Error with key sk-ant-api03-abcdefghij1234567890-ABCDEFGHIJ"
        response = create_safe_error_response(status_code=500, detail=error)
        assert "sk-ant-" not in response["detail"]

    def test_no_gemini_api_key_exposure(self):
        """Gemini API keys should never be exposed."""
        error = "Error with key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz"
        response = create_safe_error_response(status_code=500, detail=error)
        assert "AIza" not in response["detail"]

    def test_no_api_key_in_4xx_errors(self):
        """4xx errors should also not expose API keys."""
        api_keys = [
            "sk-1234567890abcdefghijklmnopqrstuvwxyz1234",
            "sk-ant-api03-abcdefghij1234567890-ABCDEFGHIJ",
            "AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz",
        ]
        for key in api_keys:
            response = create_safe_error_response(
                status_code=400,
                detail=f"Error with key {key}",
                default_message="An error occurred."
            )
            assert key[:4] not in response["detail"]

    def test_consistent_500_messages(self):
        """All 5xx errors should have consistent generic messages."""
        expected = {
            500: "An internal server error occurred. Please try again later.",
            502: "Bad gateway. Please try again later.",
            503: "Service temporarily unavailable. Please try again later.",
            504: "Gateway timeout. Please try again later.",
        }
        for status_code, expected_msg in expected.items():
            response = create_safe_error_response(
                status_code=status_code,
                detail="Sensitive internal error"
            )
            assert response["detail"] == expected_msg
            assert "correlation_id" in response

    def test_correlation_id_can_be_used_for_debugging(self):
        """Correlation ID should be usable for debugging without exposing internals."""
        response = create_safe_error_response(status_code=500, detail="Sensitive error")
        correlation_id = response["correlation_id"]

        # Correlation ID should be a valid UUID that can be logged and searched
        assert len(correlation_id) == 36  # UUID format
        assert "-" in correlation_id

        # But the response should not contain any sensitive info
        assert "Sensitive" not in response["detail"]
        assert response["detail"] == "An internal server error occurred. Please try again later."


# ============================================================
# Integration Tests
# ============================================================

class TestErrorHandlerIntegration:
    """Integration tests for error handlers."""

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

        @app.get("/raise-400-with-path")
        async def raise_400_with_path():
            raise HTTPException(
                status_code=400,
                detail="Error in /var/www/config.json"
            )

        @app.get("/raise-gemini-error")
        async def raise_gemini_error():
            raise HTTPException(
                status_code=400,
                detail="Error with key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz"
            )

        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app, raise_server_exceptions=False)

    def test_unhandled_exception_secure(self, client):
        """Unhandled exceptions should be secure."""
        response = client.get("/raise-500")
        assert response.status_code == 500
        body = response.json()
        assert "sk-" not in body["detail"]
        assert body["detail"] == "An internal server error occurred. Please try again later."
        assert "correlation_id" in body

    def test_http_500_secure(self, client):
        """HTTP 500 should be secure."""
        response = client.get("/raise-http-500")
        assert response.status_code == 500
        body = response.json()
        assert "/home/" not in body["detail"]
        assert body["detail"] == "An internal server error occurred. Please try again later."
        assert "correlation_id" in body

    def test_http_400_safe_detail(self, client):
        """HTTP 400 with safe detail should pass through."""
        response = client.get("/raise-400")
        assert response.status_code == 400
        body = response.json()
        assert body["detail"] == "Invalid email format"

    def test_http_400_path_sanitized(self, client):
        """HTTP 400 with path should be sanitized."""
        response = client.get("/raise-400-with-path")
        assert response.status_code == 400
        body = response.json()
        assert "/var/" not in body["detail"]

    def test_gemini_key_not_exposed(self, client):
        """Gemini API keys should not be exposed."""
        response = client.get("/raise-gemini-error")
        assert response.status_code == 400
        body = response.json()
        assert "AIza" not in body["detail"]
