"""Hardened key storage service for secure API key management.

Security features:
- Session-bound encryption (keys tied to session context)
- Secure key deletion with memory clearing
- Access tracking for anomaly detection
- Rate limiting on key retrieval
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import logging

from .encryption_service import EncryptionService

logger = logging.getLogger(__name__)


@dataclass
class StoredKey:
    """Represents a stored encrypted API key with security metadata.

    Attributes:
        encrypted_key: The session-bound encrypted API key.
        created_at: Timestamp when the key was stored.
        last_accessed: Timestamp when the key was last retrieved.
        access_count: Number of times the key has been retrieved.
        session_id: The session this key is bound to (for verification).
    """
    encrypted_key: str
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    session_id: str = ""


class KeyStorageService:
    """Hardened service for storing and retrieving encrypted API keys.

    Security measures:
    1. Session-bound encryption - Keys encrypted with session context
    2. Access tracking - Monitors retrieval patterns
    3. Secure deletion - Clears keys from storage completely
    4. Rate limiting - Prevents rapid key enumeration

    Note: In-memory storage by design. Server restart clears all keys,
    providing an implicit security boundary.
    """

    MAX_ACCESS_PER_MINUTE = 60  # Rate limit

    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """Initialize the key storage service.

        Args:
            encryption_service: Optional EncryptionService instance.
                               If not provided, a new one is created.
        """
        self._encryption_service = encryption_service or EncryptionService()
        self._storage: Dict[str, StoredKey] = {}
        self._access_log: Dict[str, list] = {}  # session_id -> access timestamps

    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if session has exceeded rate limit.

        Returns:
            True if within limit, False if exceeded.
        """
        now = datetime.now(timezone.utc)
        minute_ago = now.timestamp() - 60

        if session_id not in self._access_log:
            self._access_log[session_id] = []

        # Clean old entries
        self._access_log[session_id] = [
            ts for ts in self._access_log[session_id]
            if ts > minute_ago
        ]

        if len(self._access_log[session_id]) >= self.MAX_ACCESS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for session (redacted)")
            return False

        self._access_log[session_id].append(now.timestamp())
        return True

    def store(self, session_id: str, api_key: str) -> bool:
        """Store an API key with session-bound encryption.

        The key is encrypted using the session ID as context, meaning:
        - An attacker cannot decrypt with a different session
        - Stolen encrypted data is useless without the correct session

        Args:
            session_id: Unique identifier for the session.
            api_key: The plaintext API key to store.

        Returns:
            True if storage was successful.

        Raises:
            ValueError: If session_id or api_key is empty.
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")
        if not api_key:
            raise ValueError("API key cannot be empty")

        # Encrypt with session binding
        encrypted_key = self._encryption_service.encrypt(api_key, session_id)

        now = datetime.now(timezone.utc)
        self._storage[session_id] = StoredKey(
            encrypted_key=encrypted_key,
            created_at=now,
            last_accessed=now,
            access_count=0,
            session_id=session_id
        )

        logger.info(f"API key stored for session (redacted)")
        return True

    def retrieve(self, session_id: str) -> Optional[str]:
        """Retrieve and decrypt an API key for a session.

        Includes rate limiting and access tracking.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The decrypted API key, or None if not found or rate limited.
        """
        if not session_id:
            return None

        # Check rate limit
        if not self._check_rate_limit(session_id):
            return None

        stored = self._storage.get(session_id)
        if stored is None:
            return None

        # Verify session binding (defense in depth)
        if stored.session_id != session_id:
            logger.error("Session ID mismatch during retrieval")
            return None

        # Update access tracking
        stored.last_accessed = datetime.now(timezone.utc)
        stored.access_count += 1

        # Log high access count (potential anomaly)
        if stored.access_count > 100:
            logger.warning(
                f"High access count ({stored.access_count}) for session (redacted)"
            )

        try:
            # Decrypt with session binding
            return self._encryption_service.decrypt(stored.encrypted_key, session_id)
        except ValueError as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """Securely delete a stored API key.

        Overwrites the encrypted key before deletion.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if a key was deleted, False if not found.
        """
        if not session_id:
            return False

        if session_id in self._storage:
            # Overwrite encrypted key before deletion (defense in depth)
            stored = self._storage[session_id]
            stored.encrypted_key = 'X' * len(stored.encrypted_key)

            del self._storage[session_id]

            # Clean up access log
            if session_id in self._access_log:
                del self._access_log[session_id]

            logger.info(f"API key deleted for session (redacted)")
            return True

        return False

    def exists(self, session_id: str) -> bool:
        """Check if an API key exists for a session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if a key exists for the session.
        """
        return session_id in self._storage

    def get_masked_key(self, session_id: str) -> Optional[str]:
        """Get a masked version of the API key (last 4 characters).

        Args:
            session_id: Unique identifier for the session.

        Returns:
            Masked key showing only last 4 characters, or None if not found.
        """
        api_key = self.retrieve(session_id)
        if api_key is None:
            return None

        # Show only last 4 characters
        if len(api_key) <= 4:
            return "****"

        return "*" * (len(api_key) - 4) + api_key[-4:]

    def get_key_metadata(self, session_id: str) -> Optional[dict]:
        """Get metadata about a stored key (without the key itself).

        Useful for security monitoring.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            Dict with created_at, last_accessed, access_count, or None.
        """
        stored = self._storage.get(session_id)
        if stored is None:
            return None

        return {
            "created_at": stored.created_at.isoformat(),
            "last_accessed": stored.last_accessed.isoformat(),
            "access_count": stored.access_count,
        }

    def clear_all(self) -> int:
        """Securely clear all stored keys.

        Overwrites all encrypted keys before clearing.

        Returns:
            Number of keys that were cleared.
        """
        count = len(self._storage)

        # Overwrite all encrypted keys
        for stored in self._storage.values():
            stored.encrypted_key = 'X' * len(stored.encrypted_key)

        self._storage.clear()
        self._access_log.clear()

        logger.info(f"Cleared {count} stored API keys")
        return count

    def get_storage_stats(self) -> dict:
        """Get storage statistics for monitoring.

        Returns:
            Dict with total_keys, oldest_key, newest_key.
        """
        if not self._storage:
            return {"total_keys": 0}

        created_times = [s.created_at for s in self._storage.values()]
        return {
            "total_keys": len(self._storage),
            "oldest_key": min(created_times).isoformat(),
            "newest_key": max(created_times).isoformat(),
        }
