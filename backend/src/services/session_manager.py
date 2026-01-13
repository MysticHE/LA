"""Session management service with timeout and cleanup.

This module provides session lifecycle management including:
- Session creation and tracking
- Automatic timeout after 24 hours of inactivity
- Background cleanup of expired sessions
- Secure deletion of stored credentials

Implements SEC-013 from security requirements.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List
from enum import Enum


logger = logging.getLogger(__name__)


# Default session timeout: 24 hours
DEFAULT_SESSION_TIMEOUT_HOURS = 24
# Default cleanup interval: 1 hour
DEFAULT_CLEANUP_INTERVAL_HOURS = 1


class SessionStatus(str, Enum):
    """Status of a session."""
    ACTIVE = "active"
    EXPIRED = "expired"


@dataclass
class Session:
    """Represents a user session.

    Attributes:
        session_id: Unique identifier for the session.
        created_at: When the session was created.
        last_activity: When the session was last active.
        status: Current status of the session.
    """
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: SessionStatus = SessionStatus.ACTIVE

    def is_expired(self, timeout_hours: int = DEFAULT_SESSION_TIMEOUT_HOURS) -> bool:
        """Check if the session has expired.

        Args:
            timeout_hours: Number of hours after which session expires.

        Returns:
            True if the session has been inactive for longer than timeout.
        """
        if self.status == SessionStatus.EXPIRED:
            return True

        now = datetime.now(timezone.utc)
        timeout_delta = timedelta(hours=timeout_hours)
        return (now - self.last_activity) > timeout_delta

    def mark_expired(self) -> None:
        """Mark the session as expired."""
        self.status = SessionStatus.EXPIRED


class SessionManager:
    """Manages session lifecycle with automatic timeout and cleanup.

    Provides:
    - Session creation and tracking
    - Activity timestamp updates
    - Expiry detection (24 hours of inactivity)
    - Callback registration for cleanup actions

    Example:
        manager = SessionManager()

        # Register cleanup callback
        def cleanup_keys(session_id: str) -> None:
            key_storage.delete(session_id)
        manager.register_cleanup_callback(cleanup_keys)

        # Create/access session
        manager.create_session("session-123")
        manager.touch_session("session-123")  # Update activity

        # Check if expired
        if manager.is_session_expired("session-123"):
            # Handle expired session
    """

    def __init__(
        self,
        timeout_hours: int = DEFAULT_SESSION_TIMEOUT_HOURS,
        cleanup_interval_hours: int = DEFAULT_CLEANUP_INTERVAL_HOURS
    ):
        """Initialize the session manager.

        Args:
            timeout_hours: Hours of inactivity before session expires.
            cleanup_interval_hours: How often cleanup runs (in hours).
        """
        self._sessions: Dict[str, Session] = {}
        self._timeout_hours = timeout_hours
        self._cleanup_interval_hours = cleanup_interval_hours
        self._cleanup_callbacks: List[Callable[[str], None]] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    def register_cleanup_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when a session is cleaned up.

        The callback receives the session_id and should perform any
        necessary cleanup (e.g., deleting stored keys).

        Args:
            callback: Function that takes session_id as argument.
        """
        self._cleanup_callbacks.append(callback)

    def create_session(self, session_id: str) -> Session:
        """Create a new session or get existing one.

        If the session already exists, its activity is updated.
        If it's expired, a new session is created.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The Session object.
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")

        existing = self._sessions.get(session_id)
        if existing and not existing.is_expired(self._timeout_hours):
            # Update activity and return existing session
            existing.last_activity = datetime.now(timezone.utc)
            return existing

        # Create new session (or replace expired one)
        session = Session(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The Session if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def touch_session(self, session_id: str) -> bool:
        """Update the last activity time for a session.

        Args:
            session_id: The session to update.

        Returns:
            True if session was updated, False if not found or expired.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False

        if session.is_expired(self._timeout_hours):
            return False

        session.last_activity = datetime.now(timezone.utc)
        return True

    def is_session_expired(self, session_id: str) -> bool:
        """Check if a session is expired.

        Args:
            session_id: The session ID to check.

        Returns:
            True if expired or not found, False if active.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False  # Not found is not expired (let route handle missing)

        return session.is_expired(self._timeout_hours)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists (regardless of expiry status).

        Args:
            session_id: The session ID to check.

        Returns:
            True if session exists.
        """
        return session_id in self._sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and run cleanup callbacks.

        Args:
            session_id: The session to delete.

        Returns:
            True if session was deleted, False if not found.
        """
        if session_id not in self._sessions:
            return False

        # Run cleanup callbacks
        self._run_cleanup_callbacks(session_id)

        # Delete the session
        del self._sessions[session_id]
        return True

    def _run_cleanup_callbacks(self, session_id: str) -> None:
        """Run all registered cleanup callbacks for a session.

        Args:
            session_id: The session being cleaned up.
        """
        for callback in self._cleanup_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                logger.error(f"Error in cleanup callback for session {session_id[:8]}...: {e}")

    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions.

        Finds all sessions that have expired, runs cleanup callbacks,
        and removes them from the session store.

        Returns:
            Number of sessions cleaned up.
        """
        expired_ids = []

        for session_id, session in self._sessions.items():
            if session.is_expired(self._timeout_hours):
                expired_ids.append(session_id)

        for session_id in expired_ids:
            # Mark as expired first
            session = self._sessions.get(session_id)
            if session:
                session.mark_expired()

            # Run cleanup callbacks for secure deletion
            self._run_cleanup_callbacks(session_id)

            # Remove from storage
            del self._sessions[session_id]

            logger.info(f"Cleaned up expired session: {session_id[:8]}...")

        if expired_ids:
            logger.info(f"Session cleanup completed: {len(expired_ids)} sessions removed")

        return len(expired_ids)

    def get_active_session_count(self) -> int:
        """Get the count of active (non-expired) sessions.

        Returns:
            Number of active sessions.
        """
        return sum(
            1 for s in self._sessions.values()
            if not s.is_expired(self._timeout_hours)
        )

    def get_expired_session_count(self) -> int:
        """Get the count of expired sessions pending cleanup.

        Returns:
            Number of expired sessions.
        """
        return sum(
            1 for s in self._sessions.values()
            if s.is_expired(self._timeout_hours)
        )

    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task.

        This runs cleanup_expired_sessions every cleanup_interval_hours.
        """
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Session cleanup task started (interval: {self._cleanup_interval_hours}h)")

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("Session cleanup task stopped")

    async def _cleanup_loop(self) -> None:
        """Background loop that periodically cleans up expired sessions."""
        interval_seconds = self._cleanup_interval_hours * 3600

        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                if self._running:
                    self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# Global singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance.

    Returns:
        The singleton SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def set_session_manager(manager: SessionManager) -> None:
    """Set the global session manager instance (for testing).

    Args:
        manager: The SessionManager instance to use.
    """
    global _session_manager
    _session_manager = manager
