"""Tests for the encryption service."""

import pytest
import os
import base64

from src.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test suite for EncryptionService."""

    def test_encrypt_returns_string(self):
        """Test that encrypt returns a non-empty base64 string."""
        service = EncryptionService()
        encrypted = service.encrypt("test-api-key")

        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        # Should be valid base64
        base64.b64decode(encrypted)

    def test_decrypt_returns_original(self):
        """Test that decrypt returns the original plaintext."""
        service = EncryptionService()
        original = "sk-ant-api03-test-key-12345"

        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_different_each_time(self):
        """Test that encrypting same text produces different ciphertext (due to random nonce)."""
        service = EncryptionService()
        plaintext = "same-api-key"

        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert service.decrypt(encrypted1) == service.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string_raises(self):
        """Test that encrypting empty string raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt("")

    def test_decrypt_empty_string_raises(self):
        """Test that decrypting empty string raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError, match="Cannot decrypt empty string"):
            service.decrypt("")

    def test_decrypt_invalid_data_raises(self):
        """Test that decrypting invalid data raises ValueError."""
        service = EncryptionService()

        with pytest.raises(ValueError, match="Decryption failed"):
            service.decrypt("not-valid-base64!")

    def test_decrypt_tampered_data_raises(self):
        """Test that decrypting tampered data raises error (GCM authentication)."""
        service = EncryptionService()
        encrypted = service.encrypt("test-key")

        # Tamper with the encrypted data
        decoded = base64.b64decode(encrypted)
        tampered = base64.b64encode(decoded[:-1] + b'x').decode('utf-8')

        with pytest.raises(ValueError, match="Decryption failed"):
            service.decrypt(tampered)

    def test_different_keys_cannot_decrypt(self):
        """Test that different keys cannot decrypt each other's data."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        service1 = EncryptionService(key=key1)
        service2 = EncryptionService(key=key2)

        encrypted = service1.encrypt("secret")

        with pytest.raises(ValueError, match="Decryption failed"):
            service2.decrypt(encrypted)

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

        # Should be able to encrypt and decrypt
        encrypted = service.encrypt("test")
        assert service.decrypt(encrypted) == "test"

    def test_init_from_env_key(self, monkeypatch):
        """Test that key can be loaded from ENCRYPTION_KEY env var."""
        key = EncryptionService.generate_key()
        b64_key = EncryptionService.key_to_base64(key)
        monkeypatch.setenv("ENCRYPTION_KEY", b64_key)

        service = EncryptionService()

        # Encrypt with one instance
        encrypted = service.encrypt("test-from-env")

        # Create another instance with same env key
        service2 = EncryptionService()

        # Should decrypt successfully (same key)
        assert service2.decrypt(encrypted) == "test-from-env"

    def test_uses_aes_256(self):
        """Test that the service uses AES-256 (32-byte key)."""
        # AES-256 requires 32-byte key
        assert EncryptionService.KEY_SIZE == 32

    def test_encrypt_unicode_content(self):
        """Test that unicode content can be encrypted and decrypted."""
        service = EncryptionService()
        unicode_text = "API密钥-测试-🔐"

        encrypted = service.encrypt(unicode_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == unicode_text

    def test_encrypt_long_content(self):
        """Test that long content can be encrypted and decrypted."""
        service = EncryptionService()
        long_text = "x" * 10000  # 10KB of data

        encrypted = service.encrypt(long_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == long_text
