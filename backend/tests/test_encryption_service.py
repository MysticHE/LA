"""Tests for the hardened encryption service."""

import pytest
import os
import base64

from src.services.encryption_service import EncryptionService, SecureString


class TestEncryptionService:
    """Test suite for EncryptionService."""

    def test_encrypt_returns_string(self):
        """Test that encrypt returns a non-empty base64 string."""
        service = EncryptionService()
        encrypted = service.encrypt("test-api-key", "session-123")

        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        # Should be valid base64
        base64.b64decode(encrypted)

    def test_decrypt_returns_original(self):
        """Test that decrypt returns the original plaintext."""
        service = EncryptionService()
        session_id = "session-123"
        original = "sk-ant-api03-test-key-12345"

        encrypted = service.encrypt(original, session_id)
        decrypted = service.decrypt(encrypted, session_id)

        assert decrypted == original

    def test_encrypt_different_each_time(self):
        """Test that encrypting same text produces different ciphertext (due to random salt/nonce)."""
        service = EncryptionService()
        session_id = "session-123"
        plaintext = "same-api-key"

        encrypted1 = service.encrypt(plaintext, session_id)
        encrypted2 = service.encrypt(plaintext, session_id)

        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert service.decrypt(encrypted1, session_id) == plaintext
        assert service.decrypt(encrypted2, session_id) == plaintext

    def test_encrypt_empty_string_raises(self):
        """Test that encrypting empty string raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt("", "session-123")

    def test_decrypt_empty_string_raises(self):
        """Test that decrypting empty string raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError, match="Cannot decrypt empty string"):
            service.decrypt("", "session-123")

    def test_decrypt_invalid_data_raises(self):
        """Test that decrypting invalid data raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError):
            service.decrypt("not-valid-base64!", "session-123")

    def test_decrypt_tampered_data_raises(self):
        """Test that decrypting tampered data raises error (HMAC verification)."""
        service = EncryptionService()
        session_id = "session-123"
        encrypted = service.encrypt("test-key", session_id)

        # Tamper with the encrypted data
        decoded = base64.b64decode(encrypted)
        tampered = base64.b64encode(decoded[:-1] + b'x').decode('utf-8')

        with pytest.raises(ValueError):
            service.decrypt(tampered, session_id)

    def test_different_keys_cannot_decrypt(self):
        """Test that different master keys cannot decrypt each other's data."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        service1 = EncryptionService(key=key1)
        service2 = EncryptionService(key=key2)
        session_id = "session-123"

        encrypted = service1.encrypt("secret", session_id)

        with pytest.raises(ValueError):
            service2.decrypt(encrypted, session_id)

    def test_session_binding_prevents_cross_session_decrypt(self):
        """Test that encrypted data cannot be decrypted with a different session."""
        service = EncryptionService()
        session1 = "session-123"
        session2 = "session-456"
        plaintext = "secret-key"

        encrypted = service.encrypt(plaintext, session1)

        # Should decrypt with correct session
        assert service.decrypt(encrypted, session1) == plaintext

        # Should fail with different session
        with pytest.raises(ValueError):
            service.decrypt(encrypted, session2)

    def test_generate_key_returns_32_bytes(self):
        """Test that generate_key returns a 32-byte key for AES-256."""
        key = EncryptionService.generate_key()

        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_generate_key_is_random(self):
        """Test that generated keys are unique."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()

        assert key1 != key2

    def test_key_to_base64(self):
        """Test key can be converted to base64 for storage."""
        key = EncryptionService.generate_key()
        b64_key = EncryptionService.key_to_base64(key)

        assert isinstance(b64_key, str)
        assert base64.b64decode(b64_key) == key

    def test_init_with_invalid_key_size_raises(self):
        """Test that initializing with wrong key size raises ValueError."""
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            EncryptionService(key=b"too-short")

    def test_init_with_valid_key(self):
        """Test that initializing with valid 32-byte key works."""
        key = EncryptionService.generate_key()
        service = EncryptionService(key=key)
        session_id = "session-123"

        # Should be able to encrypt and decrypt
        encrypted = service.encrypt("test", session_id)
        assert service.decrypt(encrypted, session_id) == "test"

    def test_init_from_env_key(self, monkeypatch):
        """Test that key can be loaded from ENCRYPTION_KEY env var."""
        key = EncryptionService.generate_key()
        b64_key = EncryptionService.key_to_base64(key)
        monkeypatch.setenv("ENCRYPTION_KEY", b64_key)

        service = EncryptionService()
        session_id = "session-123"

        # Encrypt with one instance
        encrypted = service.encrypt("test-from-env", session_id)

        # Create another instance with same env key
        service2 = EncryptionService()

        # Should decrypt successfully (same master key)
        assert service2.decrypt(encrypted, session_id) == "test-from-env"

    def test_uses_aes_256(self):
        """Test that the service uses AES-256 (32-byte key)."""
        assert EncryptionService.KEY_SIZE == 32

    def test_encrypt_unicode_content(self):
        """Test that unicode content can be encrypted and decrypted."""
        service = EncryptionService()
        session_id = "session-123"
        unicode_text = "API密钥-测试-🔐"

        encrypted = service.encrypt(unicode_text, session_id)
        decrypted = service.decrypt(encrypted, session_id)

        assert decrypted == unicode_text

    def test_encrypt_long_content(self):
        """Test that long content can be encrypted and decrypted."""
        service = EncryptionService()
        session_id = "session-123"
        long_text = "x" * 10000  # 10KB of data

        encrypted = service.encrypt(long_text, session_id)
        decrypted = service.decrypt(encrypted, session_id)

        assert decrypted == long_text

    def test_pbkdf2_iterations(self):
        """Test that PBKDF2 uses sufficient iterations for security."""
        # OWASP recommends at least 100,000 iterations for PBKDF2-SHA256
        assert EncryptionService.PBKDF2_ITERATIONS >= 100000

    def test_empty_session_id_works(self):
        """Test that empty session ID still works (backwards compatibility)."""
        service = EncryptionService()
        plaintext = "test-key"

        encrypted = service.encrypt(plaintext, "")
        decrypted = service.decrypt(encrypted, "")

        assert decrypted == plaintext


class TestSecureString:
    """Test suite for SecureString helper."""

    def test_get_returns_value(self):
        """Test that get() returns the original value."""
        secure = SecureString("secret")
        assert secure.get() == "secret"

    def test_str_redacted(self):
        """Test that str() returns redacted placeholder."""
        secure = SecureString("secret")
        assert str(secure) == "[REDACTED]"

    def test_repr_redacted(self):
        """Test that repr() returns redacted placeholder."""
        secure = SecureString("secret")
        assert repr(secure) == "SecureString([REDACTED])"

    def test_clear_removes_value(self):
        """Test that clear() removes the stored value."""
        secure = SecureString("secret")
        secure.clear()
        assert secure.get() == ""
