"""Tests for session manager functionality.

Tests:
- Session creation and tracking
- Session timeout after 24 hours of inactivity
- Session cleanup and key deletion
- Background cleanup task
- Middleware 401 response for expired sessions
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from src.services.session_manager import (
    Session,
    SessionStatus,
    SessionManager,
    get_session_manager,
    set_session_manager,
    DEFAULT_SESSION_TIMEOUT_HOURS,
)
from src.tasks.cleanup import CleanupTask, get_cleanup_task, set_cleanup_task
from src.services.key_storage_service import KeyStorageService


class TestSession:
    """Tests for the Session dataclass."""

    def test_session_creation(self):
        """Test that sessions are created with correct defaults."""
        session = Session(session_id="test-session")

        assert session.session_id == "test-session"
        assert session.status == SessionStatus.ACTIVE
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)

    def test_session_is_not_expired_when_active(self):
        """Test that recently created sessions are not expired."""
        session = Session(session_id="test-session")

        assert not session.is_expired()

    def test_session_is_expired_after_timeout(self):
        """Test that sessions are expired after 24 hours of inactivity."""
        session = Session(session_id="test-session")
        # Set last activity to 25 hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        assert session.is_expired()

    def test_session_is_not_expired_at_boundary(self):
        """Test that sessions are not expired at exactly 24 hours."""
        session = Session(session_id="test-session")
        # Set last activity to exactly 24 hours ago (minus 1 second to be safe)
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=24, seconds=-1)

        assert not session.is_expired()

    def test_session_is_expired_when_marked(self):
        """Test that sessions marked as expired are expired."""
        session = Session(session_id="test-session")
        session.mark_expired()

        assert session.is_expired()
        assert session.status == SessionStatus.EXPIRED

    def test_session_custom_timeout(self):
        """Test that custom timeout can be specified."""
        session = Session(session_id="test-session")
        # Set last activity to 2 hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

        # Should not be expired with 24h timeout
        assert not session.is_expired(timeout_hours=24)
        # Should be expired with 1h timeout
        assert session.is_expired(timeout_hours=1)


class TestSessionManager:
    """Tests for the SessionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh session manager for each test."""
        return SessionManager(timeout_hours=24)

    def test_create_session(self, manager):
        """Test session creation."""
        session = manager.create_session("test-session")

        assert session.session_id == "test-session"
        assert session.status == SessionStatus.ACTIVE

    def test_create_session_empty_id_raises(self, manager):
        """Test that empty session ID raises ValueError."""
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            manager.create_session("")

    def test_create_session_updates_existing(self, manager):
        """Test that creating an existing session updates activity."""
        session1 = manager.create_session("test-session")
        original_activity = session1.last_activity

        # Wait a tiny bit
        import time
        time.sleep(0.01)

        session2 = manager.create_session("test-session")

        assert session2 is session1  # Same object
        assert session2.last_activity > original_activity

    def test_get_session(self, manager):
        """Test getting an existing session."""
        manager.create_session("test-session")

        session = manager.get_session("test-session")
        assert session is not None
        assert session.session_id == "test-session"

    def test_get_session_not_found(self, manager):
        """Test getting a non-existent session returns None."""
        session = manager.get_session("nonexistent")
        assert session is None

    def test_touch_session_updates_activity(self, manager):
        """Test that touch_session updates last_activity."""
        session = manager.create_session("test-session")
        original_activity = session.last_activity

        import time
        time.sleep(0.01)

        result = manager.touch_session("test-session")

        assert result is True
        assert session.last_activity > original_activity

    def test_touch_session_not_found(self, manager):
        """Test touch_session returns False for non-existent session."""
        result = manager.touch_session("nonexistent")
        assert result is False

    def test_touch_session_expired(self, manager):
        """Test touch_session returns False for expired session."""
        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        result = manager.touch_session("test-session")
        assert result is False

    def test_is_session_expired_true(self, manager):
        """Test is_session_expired returns True for expired sessions."""
        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        assert manager.is_session_expired("test-session") is True

    def test_is_session_expired_false(self, manager):
        """Test is_session_expired returns False for active sessions."""
        manager.create_session("test-session")

        assert manager.is_session_expired("test-session") is False

    def test_is_session_expired_not_found(self, manager):
        """Test is_session_expired returns False for non-existent session."""
        # Non-existent sessions are not considered expired (let routes handle)
        assert manager.is_session_expired("nonexistent") is False

    def test_session_exists(self, manager):
        """Test session_exists for existing and non-existing sessions."""
        manager.create_session("test-session")

        assert manager.session_exists("test-session") is True
        assert manager.session_exists("nonexistent") is False

    def test_delete_session(self, manager):
        """Test deleting a session."""
        manager.create_session("test-session")

        result = manager.delete_session("test-session")

        assert result is True
        assert manager.session_exists("test-session") is False

    def test_delete_session_not_found(self, manager):
        """Test deleting a non-existent session returns False."""
        result = manager.delete_session("nonexistent")
        assert result is False

    def test_cleanup_expired_sessions(self, manager):
        """Test that cleanup_expired_sessions removes expired sessions."""
        # Create active session
        manager.create_session("active-session")

        # Create expired session
        expired = manager.create_session("expired-session")
        expired.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        count = manager.cleanup_expired_sessions()

        assert count == 1
        assert manager.session_exists("active-session") is True
        assert manager.session_exists("expired-session") is False

    def test_cleanup_calls_callbacks(self, manager):
        """Test that cleanup runs registered callbacks."""
        callback = MagicMock()
        manager.register_cleanup_callback(callback)

        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        manager.cleanup_expired_sessions()

        callback.assert_called_once_with("test-session")

    def test_cleanup_callback_error_handled(self, manager):
        """Test that callback errors don't stop cleanup."""
        error_callback = MagicMock(side_effect=Exception("Test error"))
        success_callback = MagicMock()

        manager.register_cleanup_callback(error_callback)
        manager.register_cleanup_callback(success_callback)

        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Should not raise
        count = manager.cleanup_expired_sessions()

        assert count == 1
        success_callback.assert_called_once_with("test-session")

    def test_get_active_session_count(self, manager):
        """Test counting active sessions."""
        manager.create_session("session-1")
        manager.create_session("session-2")
        expired = manager.create_session("session-3")
        expired.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        assert manager.get_active_session_count() == 2

    def test_get_expired_session_count(self, manager):
        """Test counting expired sessions."""
        manager.create_session("active")
        expired1 = manager.create_session("expired-1")
        expired1.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)
        expired2 = manager.create_session("expired-2")
        expired2.last_activity = datetime.now(timezone.utc) - timedelta(hours=30)

        assert manager.get_expired_session_count() == 2


class TestSessionManagerAsync:
    """Tests for async session manager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a session manager with short intervals for testing."""
        return SessionManager(
            timeout_hours=24,
            cleanup_interval_hours=1  # 1 hour, but we'll test differently
        )

    @pytest.mark.asyncio
    async def test_start_cleanup_task(self, manager):
        """Test starting the cleanup task."""
        await manager.start_cleanup_task()

        assert manager._running is True
        assert manager._cleanup_task is not None

        await manager.stop_cleanup_task()

    @pytest.mark.asyncio
    async def test_stop_cleanup_task(self, manager):
        """Test stopping the cleanup task."""
        await manager.start_cleanup_task()
        await manager.stop_cleanup_task()

        assert manager._running is False
        assert manager._cleanup_task is None

    @pytest.mark.asyncio
    async def test_start_multiple_times(self, manager):
        """Test that starting multiple times doesn't create multiple tasks."""
        await manager.start_cleanup_task()
        task1 = manager._cleanup_task

        await manager.start_cleanup_task()
        task2 = manager._cleanup_task

        assert task1 is task2  # Same task

        await manager.stop_cleanup_task()


class TestCleanupTask:
    """Tests for the CleanupTask class."""

    @pytest.fixture
    def session_manager(self):
        """Create a session manager for testing."""
        return SessionManager(timeout_hours=24)

    @pytest.fixture
    def key_storage(self):
        """Create a key storage for testing."""
        return KeyStorageService()

    @pytest.fixture
    def cleanup_task(self, session_manager):
        """Create a cleanup task with the test session manager."""
        return CleanupTask(session_manager=session_manager)

    def test_add_key_storage(self, cleanup_task, key_storage):
        """Test adding key storage to cleanup."""
        cleanup_task.add_key_storage(key_storage)

        assert key_storage in cleanup_task._key_storages

    def test_cleanup_deletes_keys(self, cleanup_task, key_storage, session_manager):
        """Test that cleanup deletes keys from storage."""
        cleanup_task.add_key_storage(key_storage)
        cleanup_task.configure()

        # Store a key
        key_storage.store("test-session", "sk-test-key-12345")

        # Create and expire session
        session = session_manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Run cleanup
        cleanup_task.run_cleanup_now()

        # Key should be deleted
        assert not key_storage.exists("test-session")

    def test_cleanup_multiple_storages(self, cleanup_task, session_manager):
        """Test cleanup with multiple key storages."""
        storage1 = KeyStorageService()
        storage2 = KeyStorageService()

        cleanup_task.add_key_storage(storage1)
        cleanup_task.add_key_storage(storage2)
        cleanup_task.configure()

        # Store keys in both storages
        storage1.store("test-session", "sk-claude-key-123")
        storage2.store("test-session", "sk-openai-key-456")

        # Create and expire session
        session = session_manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Run cleanup
        cleanup_task.run_cleanup_now()

        # Keys should be deleted from both
        assert not storage1.exists("test-session")
        assert not storage2.exists("test-session")

    @pytest.mark.asyncio
    async def test_start_and_stop(self, cleanup_task, session_manager):
        """Test starting and stopping the cleanup task."""
        await cleanup_task.start()

        assert cleanup_task._started is True
        assert session_manager._running is True

        await cleanup_task.stop()

        assert cleanup_task._started is False
        assert session_manager._running is False


class TestSessionMiddleware:
    """Tests for the session middleware."""

    @pytest.fixture
    def session_manager(self):
        """Create a session manager for testing."""
        return SessionManager(timeout_hours=24)

    def test_expired_session_returns_401(self, session_manager):
        """Test that expired sessions return 401."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Create and expire session
        session = session_manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Make request with expired session
        response = client.get("/test", headers={"X-Session-ID": "test-session"})

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_active_session_passes_through(self, session_manager):
        """Test that active sessions pass through."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Create active session
        session_manager.create_session("test-session")

        # Make request with active session
        response = client.get("/test", headers={"X-Session-ID": "test-session"})

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_no_session_passes_through(self, session_manager):
        """Test that requests without session ID pass through."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Make request without session ID
        response = client.get("/test")

        assert response.status_code == 200

    def test_excluded_paths_pass_through(self, session_manager):
        """Test that excluded paths pass through without session check."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(
            SessionMiddleware,
            session_manager=session_manager,
            exclude_paths=["/", "/health"]
        )

        @app.get("/")
        async def root():
            return {"status": "root"}

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        client = TestClient(app)

        # Root should pass through even with expired session
        session = session_manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        response = client.get("/", headers={"X-Session-ID": "test-session"})
        assert response.status_code == 200

        response = client.get("/health", headers={"X-Session-ID": "test-session"})
        assert response.status_code == 200

    def test_new_session_created_on_first_request(self, session_manager):
        """Test that a new session is created for unknown session IDs."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Make request with new session ID
        response = client.get("/test", headers={"X-Session-ID": "new-session"})

        assert response.status_code == 200
        assert session_manager.session_exists("new-session")

    def test_session_activity_updated_on_request(self, session_manager):
        """Test that session activity is updated on each request."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=session_manager)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Create session
        session = session_manager.create_session("test-session")
        original_activity = session.last_activity

        import time
        time.sleep(0.01)

        # Make request
        client.get("/test", headers={"X-Session-ID": "test-session"})

        # Activity should be updated
        assert session.last_activity > original_activity


class TestGlobalInstances:
    """Tests for global session manager and cleanup task instances."""

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        # Reset global
        import src.services.session_manager as sm
        sm._session_manager = None

        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2

    def test_set_session_manager(self):
        """Test setting a custom session manager."""
        custom_manager = SessionManager(timeout_hours=1)
        set_session_manager(custom_manager)

        assert get_session_manager() is custom_manager

    def test_get_cleanup_task_singleton(self):
        """Test that get_cleanup_task returns singleton."""
        # Reset global
        import src.tasks.cleanup as cleanup
        cleanup._cleanup_task = None

        task1 = get_cleanup_task()
        task2 = get_cleanup_task()

        assert task1 is task2

    def test_set_cleanup_task(self):
        """Test setting a custom cleanup task."""
        custom_task = CleanupTask()
        set_cleanup_task(custom_task)

        assert get_cleanup_task() is custom_task


class TestAcceptanceCriteria:
    """Tests for the acceptance criteria of US-SEC-005."""

    def test_session_marked_expired_after_24_hours(self):
        """GIVEN a session WHEN inactive for 24 hours THEN session is marked expired."""
        manager = SessionManager(timeout_hours=24)
        session = manager.create_session("test-session")

        # Set last activity to 24+ hours ago
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=24, minutes=1)

        assert manager.is_session_expired("test-session") is True

    def test_expired_session_returns_401(self):
        """GIVEN an expired session WHEN any request is made THEN return 401 with 'session expired' message."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.middleware.session_middleware import SessionMiddleware

        manager = SessionManager(timeout_hours=24)
        app = FastAPI()
        app.add_middleware(SessionMiddleware, session_manager=manager)

        @app.get("/api/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Create and expire session
        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Make request
        response = client.get("/api/test", headers={"X-Session-ID": "test-session"})

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_expired_session_keys_securely_deleted(self):
        """GIVEN an expired session WHEN cleaned up THEN encrypted keys are securely deleted."""
        manager = SessionManager(timeout_hours=24)
        key_storage = KeyStorageService()

        cleanup = CleanupTask(session_manager=manager)
        cleanup.add_key_storage(key_storage)
        cleanup.configure()

        # Store a key
        key_storage.store("test-session", "sk-test-api-key-12345678")
        assert key_storage.exists("test-session")

        # Create and expire session
        session = manager.create_session("test-session")
        session.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)

        # Run cleanup
        cleanup.run_cleanup_now()

        # Key should be securely deleted
        assert not key_storage.exists("test-session")
        assert manager.session_exists("test-session") is False

    def test_cleanup_runs_as_background_task(self):
        """Session cleanup runs as background task every hour."""
        # Verify cleanup interval is configurable and defaults to 1 hour
        manager = SessionManager()
        assert manager._cleanup_interval_hours == 1

        # Verify we can configure different intervals
        manager2 = SessionManager(cleanup_interval_hours=2)
        assert manager2._cleanup_interval_hours == 2
