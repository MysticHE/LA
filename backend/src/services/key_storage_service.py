"""Key storage service for secure API key management.

This module provides in-memory storage of encrypted API keys,
associated with session IDs for multi-tenant support.
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from .encryption_service import EncryptionService


@dataclass
class StoredKey:
    """Represents a stored encrypted API key.

    Attributes:
        encrypted_key: The AES-256 encrypted API key.
        created_at: Timestamp when the key was stored.
        last_accessed: Timestamp when the key was last retrieved.
    """
    encrypted_key: str
    created_at: datetime
    last_accessed: datetime


class KeyStorageService:
    """Service for storing and retrieving encrypted API keys.

    Provides in-memory storage of API keys associated with session IDs.
    Keys are encrypted at rest using the EncryptionService.

    Note: This implementation uses in-memory storage. For production,
    consider using a persistent database with the same encryption approach.
    """

    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """Initialize the key storage service.

        Args:
            encryption_service: Optional EncryptionService instance.
                               If not provided, a new one is created.
        """
        self._encryption_service = encryption_service or EncryptionService()
        self._storage: Dict[str, StoredKey] = {}

    def store(self, session_id: str, api_key: str) -> bool:
        """Store an API key for a session.

        The key is encrypted before storage using AES-256-GCM.

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

        # Encrypt the key before storage
        encrypted_key = self._encryption_service.encrypt(api_key)

        now = datetime.now(timezone.utc)
        self._storage[session_id] = StoredKey(
            encrypted_key=encrypted_key,
            created_at=now,
            last_accessed=now
        )

        return True

    def retrieve(self, session_id: str) -> Optional[str]:
        """Retrieve and decrypt an API key for a session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The decrypted API key, or None if not found.
        """
        if not session_id:
            return None

        stored = self._storage.get(session_id)
        if stored is None:
            return None

        # Update last accessed time
        stored.last_accessed = datetime.now(timezone.utc)

        # Decrypt and return
        return self._encryption_service.decrypt(stored.encrypted_key)

    def delete(self, session_id: str) -> bool:
        """Delete a stored API key.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if a key was deleted, False if not found.
        """
        if not session_id:
            return False

        if session_id in self._storage:
            del self._storage[session_id]
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

    def clear_all(self) -> int:
        """Clear all stored keys.

        Returns:
            Number of keys that were cleared.
        """
        count = len(self._storage)
        self._storage.clear()
        return count
