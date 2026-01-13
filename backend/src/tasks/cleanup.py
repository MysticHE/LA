"""Background cleanup tasks for session and key management.

This module provides background tasks for:
- Session cleanup (expired sessions)
- Secure key deletion
- Periodic maintenance

Runs as a background task every hour per SEC-013 requirements.
"""

import logging
from typing import List, Callable

from src.services.session_manager import get_session_manager, SessionManager
from src.services.key_storage_service import KeyStorageService


logger = logging.getLogger(__name__)


class CleanupTask:
    """Background task for cleaning up expired sessions and keys.

    Registers cleanup callbacks with the session manager to ensure
    that when sessions expire, their associated encrypted keys are
    securely deleted.

    Example:
        # Create and configure cleanup task
        cleanup = CleanupTask()
        cleanup.add_key_storage(claude_key_storage)
        cleanup.add_key_storage(openai_key_storage)

        # Start the cleanup task (runs every hour)
        await cleanup.start()

        # Stop when shutting down
        await cleanup.stop()
    """

    def __init__(self, session_manager: SessionManager = None):
        """Initialize the cleanup task.

        Args:
            session_manager: Optional SessionManager instance.
                           If not provided, uses the global instance.
        """
        self._session_manager = session_manager or get_session_manager()
        self._key_storages: List[KeyStorageService] = []
        self._started = False

    def add_key_storage(self, storage: KeyStorageService) -> None:
        """Add a key storage service to be cleaned up on session expiry.

        When a session expires, all registered key storages will have
        the session's keys securely deleted.

        Args:
            storage: The KeyStorageService instance to register.
        """
        self._key_storages.append(storage)

    def _cleanup_session_keys(self, session_id: str) -> None:
        """Cleanup callback that deletes keys from all registered storages.

        This is called by the session manager when a session is cleaned up.

        Args:
            session_id: The session ID being cleaned up.
        """
        for storage in self._key_storages:
            try:
                if storage.exists(session_id):
                    storage.delete(session_id)
                    logger.info(f"Securely deleted keys for session: {session_id[:8]}...")
            except Exception as e:
                logger.error(f"Error deleting keys for session {session_id[:8]}...: {e}")

    def configure(self) -> None:
        """Configure the cleanup task by registering callbacks.

        Must be called after adding key storages and before starting.
        """
        # Register our cleanup callback with the session manager
        self._session_manager.register_cleanup_callback(self._cleanup_session_keys)

    async def start(self) -> None:
        """Start the background cleanup task.

        Configures the cleanup callbacks and starts the session manager's
        background cleanup loop.
        """
        if self._started:
            return

        self.configure()
        await self._session_manager.start_cleanup_task()
        self._started = True
        logger.info("Cleanup task started")

    async def stop(self) -> None:
        """Stop the background cleanup task."""
        if not self._started:
            return

        await self._session_manager.stop_cleanup_task()
        self._started = False
        logger.info("Cleanup task stopped")

    def run_cleanup_now(self) -> int:
        """Run cleanup immediately (for testing or manual trigger).

        Returns:
            Number of sessions cleaned up.
        """
        return self._session_manager.cleanup_expired_sessions()


# Global cleanup task instance
_cleanup_task: CleanupTask = None


def get_cleanup_task() -> CleanupTask:
    """Get the global cleanup task instance.

    Returns:
        The singleton CleanupTask instance.
    """
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = CleanupTask()
    return _cleanup_task


def set_cleanup_task(task: CleanupTask) -> None:
    """Set the global cleanup task instance (for testing).

    Args:
        task: The CleanupTask instance to use.
    """
    global _cleanup_task
    _cleanup_task = task
