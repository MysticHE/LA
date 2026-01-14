"""Tests for session security (US-SEC-003).

Tests for:
- Session cookie has HttpOnly, Secure, SameSite=Strict flags
- Session expires after 24 hours and API key deleted
- Protected endpoint returns 401 when no valid session
- Session disconnect triggers secure API key deletion
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, Response, Depends
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from src.services.session_service import (
    SessionService,
    CookieConfig,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_MAX_AGE,
    get_session_service,
    set_session_service,
)
from src.services.session_manager import SessionManager, Session, SessionStatus
from src.services.key_storage_service import KeyStorageService
from src.tasks.cleanup import CleanupTask
from src.middleware.session_middleware import SessionMiddleware


class TestCookieSecurityFlags:
    """Tests for session cookie security attributes."""

    @pytest.fixture
    def session_manager(self):
        """Create a fresh session manager."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def session_service(self, session_manager):
        """Create session service with test manager."""
        return SessionService(
            session_manager=session_manager,
            secure_mode=True
        )

    def test_cookie_has_httponly_flag(self, session_service):
        """GIVEN session cookie WHEN created THEN has HttpOnly flag."""
        config = session_service.get_cookie_config()
        assert config.httponly is True

    def test_cookie_has_secure_flag(self, session_service):
        """GIVEN session cookie WHEN created THEN has Secure flag."""
        config = session_service.get_cookie_config()
        assert config.secure is True

    def test_cookie_has_samesite_strict(self, session_service):
        """GIVEN session cookie WHEN created THEN has SameSite=Strict."""
        config = session_service.get_cookie_config()
        assert config.samesite == "strict"

    def test_cookie_set_with_all_security_flags(self, session_service, session_manager):
        """GIVEN session WHEN cookie is set THEN all security flags present."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.post("/login")
        async def login():
            response = JSONResponse({"status": "logged in"})
            session_service.create_session_with_cookie(response, "test-session")
            return response

        client = TestClient(app, raise_server_exceptions=True)
        response = client.post("/login")

        # Check the Set-Cookie header
        cookie_header = response.headers.get("set-cookie", "")

        # Verify security attributes
        assert "httponly" in cookie_header.lower(), "HttpOnly flag missing"
        assert "secure" in cookie_header.lower(), "Secure flag missing"
        assert "samesite=strict" in cookie_header.lower(), "SameSite=Strict missing"

    def test_cookie_config_defaults(self):
        """Test CookieConfig has secure defaults."""
        config = CookieConfig()

        assert config.httponly is True
        assert config.secure is True
        assert config.samesite == "strict"
        assert config.max_age == SESSION_COOKIE_MAX_AGE
        assert config.path == "/"

    def test_development_mode_disables_secure_flag(self, session_manager):
        """Test that development mode can disable Secure flag for local dev."""
        service = SessionService(
            session_manager=session_manager,
            secure_mode=False
        )
        config = service.get_cookie_config()

        # HttpOnly and SameSite should still be set
        assert config.httponly is True
        assert config.samesite == "strict"
        # Secure should be disabled for HTTP development
        assert config.secure is False


class TestSession24HourExpiry:
    """Tests for 24-hour session expiry with API key deletion."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager with 24h timeout."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def key_storage(self):
        """Create key storage service."""
        return KeyStorageService()

    @pytest.fixture
    def cleanup_task(self, session_manager, key_storage):
        """Create cleanup task with key storage."""
        task = CleanupTask(session_manager=session_manager)
        task.add_key_storage(key_storage)
        task.configure()
        return task

    def test_session_expires_after_24_hours(self, session_manager):
        """GIVEN session WHEN older than 24 hours THEN automatically expired."""
        session = session_manager.create_session("test-session")

        # Initially not expired
        assert session_manager.is_session_expired("test-session") is False

        # Set last activity to 24+ hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=24, minutes=1)

        # Should now be expired
        assert session_manager.is_session_expired("test-session") is True

    def test_session_not_expired_before_24_hours(self, session_manager):
        """GIVEN session WHEN less than 24 hours old THEN not expired."""
        session = session_manager.create_session("test-session")

        # Set last activity to 23 hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=23)

        # Should not be expired
        assert session_manager.is_session_expired("test-session") is False

    def test_expired_session_api_key_deleted(self, session_manager, key_storage, cleanup_task):
        """GIVEN session WHEN expires THEN encrypted API key is securely deleted."""
        # Store an API key
        key_storage.store("test-session", "sk-test-api-key-12345678")
        assert key_storage.exists("test-session")

        # Create and expire the session
        session = session_manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Run cleanup
        cleanup_task.run_cleanup_now()

        # API key should be deleted
        assert not key_storage.exists("test-session")
        # Session should be removed
        assert not session_manager.session_exists("test-session")


class TestProtectedEndpoint401:
    """Tests for 401 Unauthorized on protected endpoints."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def app(self, session_manager):
        """Create test FastAPI app with session middleware."""
        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/api/protected")
        async def protected_route():
            return {"status": "ok"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        return app

    def test_protected_endpoint_returns_401_for_expired_session(self, app, session_manager):
        """GIVEN protected endpoint WHEN expired session THEN return 401 Unauthorized."""
        client = TestClient(app)

        # Create and expire session
        session = session_manager.create_session("expired-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Make request with expired session
        response = client.get(
            "/api/protected",
            headers={"X-Session-ID": "expired-session"}
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_protected_endpoint_succeeds_with_valid_session(self, app, session_manager):
        """GIVEN protected endpoint WHEN valid session THEN request succeeds."""
        client = TestClient(app)

        # Create active session
        session_manager.create_session("valid-session")

        # Make request with valid session
        response = client.get(
            "/api/protected",
            headers={"X-Session-ID": "valid-session"}
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_public_endpoint_accessible_without_session(self, app, session_manager):
        """GIVEN public endpoint WHEN no session THEN request succeeds."""
        client = TestClient(app)

        # Health endpoint should be accessible without session
        response = client.get("/health")

        assert response.status_code == 200

    def test_new_session_created_for_unknown_session_id(self, app, session_manager):
        """GIVEN unknown session ID WHEN request made THEN new session created."""
        client = TestClient(app)

        # Make request with unknown session ID
        response = client.get(
            "/api/protected",
            headers={"X-Session-ID": "new-session"}
        )

        assert response.status_code == 200
        assert session_manager.session_exists("new-session")


class TestSessionDisconnect:
    """Tests for session disconnect and secure key deletion."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def key_storage(self):
        """Create key storage service."""
        return KeyStorageService()

    @pytest.fixture
    def session_service(self, session_manager):
        """Create session service."""
        return SessionService(session_manager=session_manager)

    @pytest.fixture
    def cleanup_task(self, session_manager, key_storage):
        """Create cleanup task with key storage."""
        task = CleanupTask(session_manager=session_manager)
        task.add_key_storage(key_storage)
        task.configure()
        return task

    def test_disconnect_deletes_session(self, session_manager):
        """GIVEN session WHEN disconnect triggered THEN session is deleted."""
        # Create session
        session_manager.create_session("test-session")
        assert session_manager.session_exists("test-session")

        # Delete session (simulating disconnect)
        session_manager.delete_session("test-session")

        # Session should be gone
        assert not session_manager.session_exists("test-session")

    def test_disconnect_securely_deletes_api_key(self, session_manager, key_storage, cleanup_task):
        """GIVEN session disconnect WHEN triggered THEN encrypted API key securely deleted."""
        # Store an API key
        key_storage.store("test-session", "sk-test-api-key-12345678")
        assert key_storage.exists("test-session")

        # Create session
        session_manager.create_session("test-session")

        # Delete session (triggers cleanup callbacks)
        session_manager.delete_session("test-session")

        # API key should be securely deleted
        assert not key_storage.exists("test-session")

    def test_session_service_disconnect(self, session_service, session_manager):
        """Test SessionService disconnect clears session and cookie."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.post("/disconnect")
        async def disconnect(request: Request):
            response = JSONResponse({"status": "disconnected"})
            session_service.disconnect(request, response)
            return response

        # Create session first
        session_manager.create_session("test-session")

        client = TestClient(app)
        client.cookies.set(SESSION_COOKIE_NAME, "test-session")

        response = client.post("/disconnect")

        assert response.status_code == 200
        # Cookie should be cleared
        assert SESSION_COOKIE_NAME not in response.cookies or response.cookies.get(SESSION_COOKIE_NAME) == ""


class TestSessionServiceIntegration:
    """Integration tests for SessionService."""

    @pytest.fixture
    def session_manager(self):
        """Create session manager."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def session_service(self, session_manager):
        """Create session service."""
        return SessionService(session_manager=session_manager)

    def test_create_session_with_cookie_flow(self, session_service, session_manager):
        """Test full flow of creating session with secure cookie."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.post("/create-session")
        async def create_session():
            response = JSONResponse({"status": "created"})
            session_service.create_session_with_cookie(response, "new-session")
            return response

        client = TestClient(app)
        response = client.post("/create-session")

        assert response.status_code == 200
        assert session_manager.session_exists("new-session")
        assert SESSION_COOKIE_NAME in response.cookies

    def test_validate_session_success(self, session_service, session_manager):
        """Test session validation succeeds for valid session."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/validate")
        async def validate(request: Request):
            is_valid, error = session_service.validate_session(request)
            return {"valid": is_valid, "error": error}

        # Create session
        session_manager.create_session("valid-session")

        client = TestClient(app)
        client.cookies.set(SESSION_COOKIE_NAME, "valid-session")

        response = client.get("/validate")

        assert response.status_code == 200
        assert response.json()["valid"] is True
        assert response.json()["error"] is None

    def test_validate_session_expired(self, session_service, session_manager):
        """Test session validation fails for expired session."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/validate")
        async def validate(request: Request):
            is_valid, error = session_service.validate_session(request)
            return {"valid": is_valid, "error": error}

        # Create and expire session
        session = session_manager.create_session("expired-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        client = TestClient(app)
        client.cookies.set(SESSION_COOKIE_NAME, "expired-session")

        response = client.get("/validate")

        assert response.status_code == 200
        assert response.json()["valid"] is False
        assert "expired" in response.json()["error"].lower()

    def test_validate_session_no_cookie(self, session_service):
        """Test session validation fails without cookie."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/validate")
        async def validate(request: Request):
            is_valid, error = session_service.validate_session(request)
            return {"valid": is_valid, "error": error}

        client = TestClient(app)
        response = client.get("/validate")

        assert response.status_code == 200
        assert response.json()["valid"] is False
        assert "no session" in response.json()["error"].lower()


class TestGlobalSessionService:
    """Tests for global session service singleton."""

    def test_get_session_service_singleton(self):
        """Test that get_session_service returns singleton."""
        import src.services.session_service as ss
        ss._session_service = None

        service1 = get_session_service()
        service2 = get_session_service()

        assert service1 is service2

    def test_set_session_service(self):
        """Test setting custom session service."""
        custom_service = SessionService(secure_mode=False)
        set_session_service(custom_service)

        assert get_session_service() is custom_service


class TestAcceptanceCriteria:
    """Acceptance criteria tests for US-SEC-003."""

    def test_ac1_session_cookie_has_security_flags(self):
        """
        GIVEN session cookie WHEN created
        THEN has HttpOnly, Secure, SameSite=Strict flags.
        """
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        session_manager = SessionManager(timeout_hours=24)
        session_service = SessionService(
            session_manager=session_manager,
            secure_mode=True
        )

        app = FastAPI()

        @app.post("/login")
        async def login():
            response = JSONResponse({"status": "ok"})
            session_service.create_session_with_cookie(response, "test-session")
            return response

        client = TestClient(app)
        response = client.post("/login")

        cookie_header = response.headers.get("set-cookie", "").lower()

        assert "httponly" in cookie_header
        assert "secure" in cookie_header
        assert "samesite=strict" in cookie_header

    def test_ac2_session_expires_after_24_hours_and_key_deleted(self):
        """
        GIVEN session WHEN older than 24 hours
        THEN automatically expired and API key deleted.
        """
        session_manager = SessionManager(timeout_hours=24)
        key_storage = KeyStorageService()

        cleanup_task = CleanupTask(session_manager=session_manager)
        cleanup_task.add_key_storage(key_storage)
        cleanup_task.configure()

        # Store API key and create session
        key_storage.store("test-session", "sk-test-key-12345")
        session = session_manager.create_session("test-session")

        # Set session to 25 hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Verify expired
        assert session_manager.is_session_expired("test-session")

        # Run cleanup
        cleanup_task.run_cleanup_now()

        # Key should be deleted
        assert not key_storage.exists("test-session")

    def test_ac3_protected_endpoint_returns_401_without_valid_session(self):
        """
        GIVEN protected endpoint WHEN no valid session
        THEN return 401 Unauthorized.
        """
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        session_manager = SessionManager(timeout_hours=24)
        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/api/protected")
        async def protected():
            return {"data": "secret"}

        client = TestClient(app)

        # Create expired session
        session = session_manager.create_session("expired-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Request with expired session should get 401
        response = client.get(
            "/api/protected",
            headers={"X-Session-ID": "expired-session"}
        )

        assert response.status_code == 401

    def test_ac4_session_disconnect_deletes_encrypted_key(self):
        """
        GIVEN session disconnect WHEN triggered
        THEN encrypted API key securely deleted.
        """
        session_manager = SessionManager(timeout_hours=24)
        key_storage = KeyStorageService()

        cleanup_task = CleanupTask(session_manager=session_manager)
        cleanup_task.add_key_storage(key_storage)
        cleanup_task.configure()

        # Store API key
        key_storage.store("disconnect-session", "sk-test-key-123456")
        assert key_storage.exists("disconnect-session")

        # Create session
        session_manager.create_session("disconnect-session")

        # Simulate disconnect by deleting session
        session_manager.delete_session("disconnect-session")

        # Key should be securely deleted
        assert not key_storage.exists("disconnect-session")
