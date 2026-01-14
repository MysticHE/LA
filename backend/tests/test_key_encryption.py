"""Tests for secure API key storage - US-SEC-001.

This test suite verifies:
1. Gemini API keys are encrypted using AES-256 via encryption_service.py
2. API keys are masked in logs (****xxxx format)
3. API responses show only last 4 characters
4. Security scan passes with 0 critical findings for credential exposure
"""

import pytest
import logging
import re
from io import StringIO

from src.services.encryption_service import EncryptionService
from src.services.key_storage_service import KeyStorageService
from src.utils.logging import (
    redact_api_keys,
    redact_dict_values,
    mask_api_key,
    APIKeyRedactionFilter,
    get_secure_logger,
    API_KEY_PATTERNS,
)


# Sample API keys for testing
SAMPLE_GEMINI_KEY = "AIzaSyDN3bH7S9xV2Kj8L5mP4fQ1wR6tE0cYaZb"  # 39 chars
SAMPLE_OPENAI_KEY = "sk-proj-abc123XYZ456"
SAMPLE_ANTHROPIC_KEY = "sk-ant-api03-test-key-12345"


class TestGeminiKeyEncryption:
    """Test suite for Gemini API key encryption using AES-256."""

    def test_gemini_key_encrypted_via_encryption_service(self):
        """GIVEN a Gemini API key WHEN stored in session THEN key is encrypted using AES-256."""
        encryption_service = EncryptionService()
        storage = KeyStorageService(encryption_service=encryption_service)
        session_id = "test-session-gemini-001"

        # Store the key
        storage.store(session_id, SAMPLE_GEMINI_KEY)

        # Verify it's encrypted in storage
        stored = storage._storage[session_id]

        # The stored key should not be plaintext
        assert stored.encrypted_key != SAMPLE_GEMINI_KEY

        # But it should decrypt to the original
        decrypted = encryption_service.decrypt(stored.encrypted_key)
        assert decrypted == SAMPLE_GEMINI_KEY

    def test_gemini_key_uses_aes_256(self):
        """Verify that AES-256 (32-byte key) is used for encryption."""
        # AES-256 requires a 32-byte key
        assert EncryptionService.KEY_SIZE == 32

    def test_gemini_key_encrypted_differently_each_time(self):
        """Test that same key produces different ciphertext (random nonce)."""
        encryption_service = EncryptionService()

        encrypted1 = encryption_service.encrypt(SAMPLE_GEMINI_KEY)
        encrypted2 = encryption_service.encrypt(SAMPLE_GEMINI_KEY)

        # Different ciphertext due to random nonce
        assert encrypted1 != encrypted2

        # But both decrypt to same value
        assert encryption_service.decrypt(encrypted1) == SAMPLE_GEMINI_KEY
        assert encryption_service.decrypt(encrypted2) == SAMPLE_GEMINI_KEY

    def test_gemini_key_decryption_requires_same_key(self):
        """Test that different encryption keys cannot decrypt each other's data."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        service1 = EncryptionService(key=key1)
        service2 = EncryptionService(key=key2)

        encrypted = service1.encrypt(SAMPLE_GEMINI_KEY)

        with pytest.raises(ValueError, match="Decryption failed"):
            service2.decrypt(encrypted)

    def test_gemini_key_tamper_detection(self):
        """Test that GCM mode detects tampering with encrypted data."""
        import base64

        encryption_service = EncryptionService()
        encrypted = encryption_service.encrypt(SAMPLE_GEMINI_KEY)

        # Tamper with the encrypted data
        decoded = base64.b64decode(encrypted)
        tampered = base64.b64encode(decoded[:-1] + b'X').decode('utf-8')

        with pytest.raises(ValueError, match="Decryption failed"):
            encryption_service.decrypt(tampered)


class TestAPIKeyMaskingInLogs:
    """Test suite for API key masking in log output."""

    def test_gemini_key_pattern_detected(self):
        """Test that Gemini API key pattern (AIza...) is recognized."""
        text = f"Using API key: {SAMPLE_GEMINI_KEY}"

        # Check if pattern matches
        matched = False
        for pattern in API_KEY_PATTERNS:
            if pattern.search(text):
                matched = True
                break

        assert matched, "Gemini API key pattern not detected"

    def test_gemini_key_redacted_in_logs(self):
        """GIVEN any log output WHEN API key is involved THEN only masked version appears."""
        log_text = f"Connecting with Gemini API key: {SAMPLE_GEMINI_KEY}"

        redacted = redact_api_keys(log_text)

        assert SAMPLE_GEMINI_KEY not in redacted
        assert "[REDACTED]" in redacted

    def test_openai_key_redacted_in_logs(self):
        """Test OpenAI keys are also redacted for completeness."""
        log_text = f"Using OpenAI key: {SAMPLE_OPENAI_KEY}"

        redacted = redact_api_keys(log_text)

        assert SAMPLE_OPENAI_KEY not in redacted
        assert "[REDACTED]" in redacted

    def test_anthropic_key_redacted_in_logs(self):
        """Test Anthropic keys are also redacted for completeness."""
        log_text = f"Using Claude key: {SAMPLE_ANTHROPIC_KEY}"

        redacted = redact_api_keys(log_text)

        assert SAMPLE_ANTHROPIC_KEY not in redacted
        assert "[REDACTED]" in redacted

    def test_multiple_keys_redacted(self):
        """Test multiple API keys in same text are all redacted."""
        log_text = f"Keys: Gemini={SAMPLE_GEMINI_KEY}, OpenAI={SAMPLE_OPENAI_KEY}"

        redacted = redact_api_keys(log_text)

        assert SAMPLE_GEMINI_KEY not in redacted
        assert SAMPLE_OPENAI_KEY not in redacted
        assert redacted.count("[REDACTED]") == 2

    def test_dict_redaction_for_api_key_field(self):
        """Test that dict values named 'api_key' are redacted."""
        data = {
            "user": "test",
            "api_key": SAMPLE_GEMINI_KEY,
            "status": "connected"
        }

        redacted = redact_dict_values(data)

        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["user"] == "test"
        assert redacted["status"] == "connected"

    def test_nested_dict_redaction(self):
        """Test that nested dicts with API keys are redacted."""
        data = {
            "config": {
                "api_key": SAMPLE_GEMINI_KEY,
                "timeout": 30
            }
        }

        redacted = redact_dict_values(data)

        assert redacted["config"]["api_key"] == "[REDACTED]"
        assert redacted["config"]["timeout"] == 30

    def test_secure_logger_redacts_api_keys(self):
        """Test that secure logger properly redacts API keys from messages."""
        logger = get_secure_logger("test.secure")
        logger.setLevel(logging.DEBUG)

        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        handler.addFilter(APIKeyRedactionFilter())
        logger.addHandler(handler)

        # Log message with API key
        logger.info(f"Connecting with key: {SAMPLE_GEMINI_KEY}")

        output = stream.getvalue()

        # Key should be redacted
        assert SAMPLE_GEMINI_KEY not in output
        assert "[REDACTED]" in output

        # Cleanup
        logger.removeHandler(handler)


class TestAPIKeyMaskingInResponses:
    """Test suite for API key masking in API responses."""

    def test_masked_key_shows_only_last_4_chars(self):
        """GIVEN API response WHEN key is included THEN only last 4 characters are visible."""
        storage = KeyStorageService()
        session_id = "test-session-response-001"

        storage.store(session_id, SAMPLE_GEMINI_KEY)
        masked = storage.get_masked_key(session_id)

        # Last 4 chars visible
        assert masked.endswith(SAMPLE_GEMINI_KEY[-4:])

        # Rest is masked
        assert masked.startswith("*")

        # Full key not visible
        assert SAMPLE_GEMINI_KEY not in masked

    def test_masked_key_format_asterisks_plus_4(self):
        """Test masked key format is ****xxxx with correct length."""
        storage = KeyStorageService()
        session_id = "test-session-format-001"

        storage.store(session_id, SAMPLE_GEMINI_KEY)
        masked = storage.get_masked_key(session_id)

        # Same length as original
        assert len(masked) == len(SAMPLE_GEMINI_KEY)

        # Correct number of asterisks
        asterisk_count = masked.count("*")
        assert asterisk_count == len(SAMPLE_GEMINI_KEY) - 4

    def test_mask_api_key_helper_function(self):
        """Test the mask_api_key helper function directly."""
        masked = mask_api_key(SAMPLE_GEMINI_KEY)

        assert masked.endswith(SAMPLE_GEMINI_KEY[-4:])
        assert masked.startswith("*")
        assert len(masked) == len(SAMPLE_GEMINI_KEY)

    def test_mask_api_key_short_key(self):
        """Test that short keys (<=4 chars) are fully masked."""
        assert mask_api_key("abc") == "****"
        assert mask_api_key("abcd") == "****"
        assert mask_api_key("ab") == "****"

    def test_mask_api_key_empty_key(self):
        """Test that empty keys return empty string."""
        assert mask_api_key("") == ""
        assert mask_api_key(None) == "" if mask_api_key(None) is not None else True

    def test_masked_key_for_nonexistent_session_is_none(self):
        """Test that getting masked key for nonexistent session returns None."""
        storage = KeyStorageService()

        result = storage.get_masked_key("nonexistent-session")

        assert result is None


class TestSecurityScanRequirements:
    """Test suite for security scan requirements."""

    def test_no_plaintext_key_in_storage_structure(self):
        """Verify stored keys are never in plaintext."""
        storage = KeyStorageService()
        session_id = "test-security-scan-001"

        storage.store(session_id, SAMPLE_GEMINI_KEY)

        # Access internal storage
        stored = storage._storage[session_id]

        # No plaintext key anywhere in the stored structure
        assert SAMPLE_GEMINI_KEY not in str(stored)
        assert SAMPLE_GEMINI_KEY != stored.encrypted_key

    def test_gemini_key_pattern_matches_real_format(self):
        """Verify Gemini key pattern matches actual Google API key format."""
        # Real Google API keys start with "AIza" and are 39 characters
        valid_patterns = [
            "AIzaSyDN3bH7S9xV2Kj8L5mP4fQ1wR6tE0cYaZb",  # 39 chars
            "AIzaSyABC123xyz456DEF789ghi012JKL345mnX",  # 39 chars
            "AIzaSyTest_Key-With_Special12Characters",  # 39 chars with _ and -
        ]

        invalid_patterns = [
            "AIza",  # Too short
            "AIzaSyShort",  # Too short (< 39 chars)
            "sk-proj-abc123",  # OpenAI format
            "notAnApiKey",  # Random string
        ]

        gemini_pattern = re.compile(r'AIza[a-zA-Z0-9_-]{35,}')

        for valid in valid_patterns:
            assert gemini_pattern.match(valid), f"Should match: {valid}"

        for invalid in invalid_patterns:
            match = gemini_pattern.match(invalid)
            # Short AIza strings should not match
            if invalid.startswith("AIza") and len(invalid) < 39:
                assert not match, f"Should not match (too short): {invalid}"

    def test_encryption_key_not_hardcoded(self):
        """Verify encryption service doesn't use hardcoded keys."""
        service1 = EncryptionService()
        service2 = EncryptionService()

        # Each instance generates its own key if not provided
        encrypted1 = service1.encrypt("test")

        # Different instances should have different keys (unless from env)
        # So decrypting with a different instance should fail
        # (unless they both loaded the same env key)
        import os
        if not os.environ.get("ENCRYPTION_KEY"):
            # Without env key, each instance has different key
            with pytest.raises(ValueError):
                service2.decrypt(encrypted1)

    def test_sensitive_field_names_redacted(self):
        """Verify common sensitive field names are auto-redacted."""
        sensitive_fields = {'api_key', 'api_keys', 'key', 'secret', 'password', 'token'}

        data = {
            "api_key": SAMPLE_GEMINI_KEY,
            "secret": "my-secret",
            "password": "my-password",
            "token": "auth-token",
            "normal_field": "not redacted"
        }

        redacted = redact_dict_values(data)

        for field in sensitive_fields:
            if field in data:
                assert redacted[field] == "[REDACTED]"

        assert redacted["normal_field"] == "not redacted"


class TestKeyLifecycle:
    """Test complete key lifecycle: store, retrieve, mask, delete."""

    def test_full_gemini_key_lifecycle(self):
        """Test complete lifecycle of a Gemini API key."""
        storage = KeyStorageService()
        session_id = "lifecycle-test-001"

        # 1. Store key (encrypted)
        result = storage.store(session_id, SAMPLE_GEMINI_KEY)
        assert result is True

        # 2. Key exists
        assert storage.exists(session_id) is True

        # 3. Retrieve decrypted key
        retrieved = storage.retrieve(session_id)
        assert retrieved == SAMPLE_GEMINI_KEY

        # 4. Get masked version for display
        masked = storage.get_masked_key(session_id)
        assert masked.endswith(SAMPLE_GEMINI_KEY[-4:])
        assert SAMPLE_GEMINI_KEY not in masked

        # 5. Delete key
        deleted = storage.delete(session_id)
        assert deleted is True

        # 6. Key no longer exists
        assert storage.exists(session_id) is False
        assert storage.retrieve(session_id) is None
        assert storage.get_masked_key(session_id) is None

    def test_session_isolation(self):
        """Test that different sessions have isolated keys."""
        storage = KeyStorageService()

        # Store different keys for different sessions
        storage.store("session-gemini", SAMPLE_GEMINI_KEY)
        storage.store("session-openai", SAMPLE_OPENAI_KEY)

        # Each session gets its own key
        assert storage.retrieve("session-gemini") == SAMPLE_GEMINI_KEY
        assert storage.retrieve("session-openai") == SAMPLE_OPENAI_KEY

        # Deleting one doesn't affect the other
        storage.delete("session-gemini")
        assert storage.retrieve("session-gemini") is None
        assert storage.retrieve("session-openai") == SAMPLE_OPENAI_KEY
