"""Tests for the hardened key storage service."""

import pytest
from datetime import datetime, timezone

from src.services.key_storage_service import KeyStorageService, StoredKey
from src.services.encryption_service import EncryptionService


class TestKeyStorageService:
    """Test suite for KeyStorageService."""

    def test_store_and_retrieve_key(self):
        """Test that a key can be stored and retrieved."""
        service = KeyStorageService()
        session_id = "session-123"
        api_key = "sk-ant-api03-test-key"

        result = service.store(session_id, api_key)
        retrieved = service.retrieve(session_id)

        assert result is True
        assert retrieved == api_key

    def test_store_encrypts_key_with_session_binding(self):
        """Test that the key is encrypted with session binding when stored."""
        encryption_service = EncryptionService()
        storage_service = KeyStorageService(encryption_service=encryption_service)

        session_id = "session-123"
        api_key = "sk-ant-api03-test-key"

        storage_service.store(session_id, api_key)

        # Access internal storage to verify encryption
        stored = storage_service._storage[session_id]

        # The stored key should not be the plaintext
        assert stored.encrypted_key != api_key
        # But it should decrypt to the original with correct session
        assert encryption_service.decrypt(stored.encrypted_key, session_id) == api_key

    def test_session_bound_encryption_prevents_cross_session_access(self):
        """Test that encrypted keys cannot be decrypted with wrong session."""
        encryption_service = EncryptionService()
        storage_service = KeyStorageService(encryption_service=encryption_service)

        session_id = "session-123"
        wrong_session = "session-456"
        api_key = "sk-ant-api03-test-key"

        storage_service.store(session_id, api_key)

        # Access internal storage
        stored = storage_service._storage[session_id]

        # Should fail to decrypt with wrong session
        with pytest.raises(ValueError):
            encryption_service.decrypt(stored.encrypted_key, wrong_session)

    def test_retrieve_nonexistent_returns_none(self):
        """Test that retrieving a nonexistent key returns None."""
        service = KeyStorageService()

        result = service.retrieve("nonexistent-session")

        assert result is None

    def test_retrieve_empty_session_returns_none(self):
        """Test that retrieving with empty session ID returns None."""
        service = KeyStorageService()

        result = service.retrieve("")

        assert result is None

    def test_store_empty_session_raises(self):
        """Test that storing with empty session ID raises ValueError."""
        service = KeyStorageService()

        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            service.store("", "api-key")

    def test_store_empty_key_raises(self):
        """Test that storing with empty API key raises ValueError."""
        service = KeyStorageService()

        with pytest.raises(ValueError, match="API key cannot be empty"):
            service.store("session-123", "")

    def test_delete_existing_key(self):
        """Test that an existing key can be deleted."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")

        result = service.delete(session_id)

        assert result is True
        assert service.retrieve(session_id) is None

    def test_delete_nonexistent_returns_false(self):
        """Test that deleting a nonexistent key returns False."""
        service = KeyStorageService()

        result = service.delete("nonexistent")

        assert result is False

    def test_delete_empty_session_returns_false(self):
        """Test that deleting with empty session ID returns False."""
        service = KeyStorageService()

        result = service.delete("")

        assert result is False

    def test_exists_returns_true_for_stored_key(self):
        """Test that exists returns True for a stored key."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")

        assert service.exists(session_id) is True

    def test_exists_returns_false_for_missing_key(self):
        """Test that exists returns False for a missing key."""
        service = KeyStorageService()

        assert service.exists("nonexistent") is False

    def test_get_masked_key(self):
        """Test that masked key shows only last 4 characters."""
        service = KeyStorageService()
        session_id = "session-123"
        api_key = "sk-ant-api03-test-key-12345"

        service.store(session_id, api_key)
        masked = service.get_masked_key(session_id)

        assert masked is not None
        assert masked.endswith("2345")
        assert masked.startswith("*")
        assert api_key not in masked  # Full key should not be visible
        assert len(masked) == len(api_key)

    def test_get_masked_key_short_key(self):
        """Test that short keys are fully masked."""
        service = KeyStorageService()
        session_id = "session-123"
        api_key = "abc"  # Less than 4 characters

        service.store(session_id, api_key)
        masked = service.get_masked_key(session_id)

        assert masked == "****"

    def test_get_masked_key_nonexistent_returns_none(self):
        """Test that masked key for nonexistent session returns None."""
        service = KeyStorageService()

        result = service.get_masked_key("nonexistent")

        assert result is None

    def test_clear_all(self):
        """Test that clear_all removes all stored keys."""
        service = KeyStorageService()
        service.store("session-1", "key-1")
        service.store("session-2", "key-2")
        service.store("session-3", "key-3")

        count = service.clear_all()

        assert count == 3
        assert service.retrieve("session-1") is None
        assert service.retrieve("session-2") is None
        assert service.retrieve("session-3") is None

    def test_clear_all_empty_storage(self):
        """Test that clear_all on empty storage returns 0."""
        service = KeyStorageService()

        count = service.clear_all()

        assert count == 0

    def test_overwrite_existing_key(self):
        """Test that storing for existing session overwrites the key."""
        service = KeyStorageService()
        session_id = "session-123"

        service.store(session_id, "old-key")
        service.store(session_id, "new-key")

        assert service.retrieve(session_id) == "new-key"

    def test_multiple_sessions_isolated(self):
        """Test that multiple sessions have isolated keys."""
        service = KeyStorageService()

        service.store("session-1", "key-1")
        service.store("session-2", "key-2")

        assert service.retrieve("session-1") == "key-1"
        assert service.retrieve("session-2") == "key-2"

        # Deleting one doesn't affect the other
        service.delete("session-1")
        assert service.retrieve("session-1") is None
        assert service.retrieve("session-2") == "key-2"

    def test_stored_key_has_timestamps(self):
        """Test that stored keys have created_at and last_accessed timestamps."""
        service = KeyStorageService()
        session_id = "session-123"

        before = datetime.now(timezone.utc)
        service.store(session_id, "api-key")
        after = datetime.now(timezone.utc)

        stored = service._storage[session_id]

        assert stored.created_at >= before
        assert stored.created_at <= after
        assert stored.last_accessed >= before
        assert stored.last_accessed <= after

    def test_retrieve_updates_last_accessed(self):
        """Test that retrieving a key updates its last_accessed timestamp."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")

        initial_access = service._storage[session_id].last_accessed

        # Wait a tiny bit and retrieve
        import time
        time.sleep(0.01)
        service.retrieve(session_id)

        updated_access = service._storage[session_id].last_accessed

        assert updated_access > initial_access

    def test_retrieve_increments_access_count(self):
        """Test that retrieving a key increments the access count."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")

        assert service._storage[session_id].access_count == 0

        service.retrieve(session_id)
        assert service._storage[session_id].access_count == 1

        service.retrieve(session_id)
        assert service._storage[session_id].access_count == 2

    def test_get_key_metadata(self):
        """Test that key metadata can be retrieved."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")
        service.retrieve(session_id)  # Increment access count

        metadata = service.get_key_metadata(session_id)

        assert metadata is not None
        assert "created_at" in metadata
        assert "last_accessed" in metadata
        assert "access_count" in metadata
        assert metadata["access_count"] == 1

    def test_get_key_metadata_nonexistent(self):
        """Test that metadata for nonexistent session returns None."""
        service = KeyStorageService()

        metadata = service.get_key_metadata("nonexistent")

        assert metadata is None

    def test_get_storage_stats(self):
        """Test that storage stats can be retrieved."""
        service = KeyStorageService()
        service.store("session-1", "key-1")
        service.store("session-2", "key-2")

        stats = service.get_storage_stats()

        assert stats["total_keys"] == 2
        assert "oldest_key" in stats
        assert "newest_key" in stats

    def test_get_storage_stats_empty(self):
        """Test that storage stats for empty storage."""
        service = KeyStorageService()

        stats = service.get_storage_stats()

        assert stats["total_keys"] == 0

    def test_stored_key_has_session_id(self):
        """Test that stored key records the session ID for verification."""
        service = KeyStorageService()
        session_id = "session-123"
        service.store(session_id, "api-key")

        stored = service._storage[session_id]
        assert stored.session_id == session_id

    def test_shared_encryption_service(self):
        """Test that a shared encryption service can be used."""
        encryption_service = EncryptionService()
        storage1 = KeyStorageService(encryption_service=encryption_service)
        storage2 = KeyStorageService(encryption_service=encryption_service)

        session_id = "session-123"

        # Store with one service
        storage1.store(session_id, "api-key")

        # Can't retrieve from another storage instance (different in-memory storage)
        assert storage2.retrieve(session_id) is None

        # But if we manually copy the encrypted data, it can be decrypted with correct session
        encrypted = storage1._storage[session_id].encrypted_key
        decrypted = encryption_service.decrypt(encrypted, session_id)
        assert decrypted == "api-key"
