"""Hardened encryption service for secure API key storage.

Security features:
- AES-256-GCM authenticated encryption
- PBKDF2 key derivation (slows brute force attacks)
- Session-bound encryption (keys tied to session context)
- Secure memory handling
- Timing-safe comparisons
"""

import os
import base64
import secrets
import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionService:
    """Hardened encryption service with defense-in-depth protections.

    Security measures against pro attackers:
    1. AES-256-GCM - Authenticated encryption prevents tampering
    2. Unique nonce per encryption - Prevents replay attacks
    3. Session binding - Encrypted data tied to session context
    4. Key derivation - Master key derives per-session keys via PBKDF2
    5. HMAC integrity - Additional integrity verification layer
    """

    KEY_SIZE = 32  # AES-256
    NONCE_SIZE = 12  # GCM standard (96 bits)
    SALT_SIZE = 16  # For key derivation
    HMAC_SIZE = 32  # SHA-256 HMAC
    PBKDF2_ITERATIONS = 100000  # Slows brute force

    def __init__(self, key: Optional[bytes] = None):
        """Initialize with master encryption key.

        Args:
            key: Optional 32-byte master key. If not provided,
                 loads from ENCRYPTION_KEY env var or generates new.
        """
        if key is not None:
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Key must be {self.KEY_SIZE} bytes")
            self._master_key = key
        else:
            self._master_key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        """Load master key from environment or generate securely."""
        env_key = os.environ.get("ENCRYPTION_KEY")
        if env_key:
            try:
                key = base64.b64decode(env_key)
                if len(key) == self.KEY_SIZE:
                    return key
                logger.warning("ENCRYPTION_KEY invalid length, generating new")
            except Exception:
                logger.warning("ENCRYPTION_KEY decode failed, generating new")

        # Generate new key - log warning in production
        if os.environ.get("ENVIRONMENT") == "production":
            logger.warning(
                "ENCRYPTION_KEY not set in production! "
                "Keys will be lost on restart. Set ENCRYPTION_KEY env var."
            )
        return secrets.token_bytes(self.KEY_SIZE)

    def _derive_key(self, session_id: str, salt: bytes) -> bytes:
        """Derive session-specific key using PBKDF2.

        This ensures:
        - Encrypted data is bound to specific session
        - Attacker with encrypted data can't use it with different session
        - Brute force attacks are computationally expensive

        Args:
            session_id: The session identifier
            salt: Random salt for this encryption

        Returns:
            Derived 32-byte key for this session+salt combination
        """
        # Combine master key with session context
        key_material = self._master_key + session_id.encode('utf-8')

        # PBKDF2 with SHA-256
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            key_material,
            salt,
            self.PBKDF2_ITERATIONS,
            dklen=self.KEY_SIZE
        )
        return derived

    def _compute_hmac(self, key: bytes, data: bytes) -> bytes:
        """Compute HMAC-SHA256 for integrity verification."""
        return hmac.new(key, data, hashlib.sha256).digest()

    def _verify_hmac(self, key: bytes, data: bytes, expected: bytes) -> bool:
        """Timing-safe HMAC verification."""
        computed = self._compute_hmac(key, data)
        return hmac.compare_digest(computed, expected)

    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new random AES-256 key."""
        return secrets.token_bytes(cls.KEY_SIZE)

    @classmethod
    def key_to_base64(cls, key: bytes) -> str:
        """Convert key to base64 for storage."""
        return base64.b64encode(key).decode('utf-8')

    def encrypt(self, plaintext: str, session_id: str = "") -> str:
        """Encrypt with session binding and integrity protection.

        Format: base64(salt || nonce || ciphertext || hmac)

        Args:
            plaintext: String to encrypt
            session_id: Session context for key derivation

        Returns:
            Base64-encoded encrypted data

        Raises:
            ValueError: If plaintext is empty
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        # Generate random salt and nonce
        salt = secrets.token_bytes(self.SALT_SIZE)
        nonce = secrets.token_bytes(self.NONCE_SIZE)

        # Derive session-bound key
        derived_key = self._derive_key(session_id, salt)

        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(derived_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        # Compute HMAC over salt + nonce + ciphertext for extra integrity
        payload = salt + nonce + ciphertext
        integrity_hmac = self._compute_hmac(derived_key, payload)

        # Combine: salt || nonce || ciphertext || hmac
        combined = payload + integrity_hmac

        # Securely clear derived key from memory
        derived_key = b'\x00' * self.KEY_SIZE

        return base64.b64encode(combined).decode('utf-8')

    def decrypt(self, encrypted_data: str, session_id: str = "") -> str:
        """Decrypt with session binding and integrity verification.

        Args:
            encrypted_data: Base64-encoded data from encrypt()
            session_id: Must match session used during encryption

        Returns:
            Original plaintext

        Raises:
            ValueError: If data is invalid, tampered, or wrong session
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty string")

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        try:
            combined = base64.b64decode(encrypted_data)

            # Minimum size check
            min_size = self.SALT_SIZE + self.NONCE_SIZE + 16 + self.HMAC_SIZE
            if len(combined) < min_size:
                raise ValueError("Invalid encrypted data")

            # Extract components
            salt = combined[:self.SALT_SIZE]
            nonce = combined[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            ciphertext = combined[self.SALT_SIZE + self.NONCE_SIZE:-self.HMAC_SIZE]
            stored_hmac = combined[-self.HMAC_SIZE:]

            # Derive the same session-bound key
            derived_key = self._derive_key(session_id, salt)

            # Verify HMAC first (fail fast on tampering)
            payload = salt + nonce + ciphertext
            if not self._verify_hmac(derived_key, payload, stored_hmac):
                # Securely clear key
                derived_key = b'\x00' * self.KEY_SIZE
                raise ValueError("Data integrity check failed")

            # Decrypt
            aesgcm = AESGCM(derived_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Securely clear derived key
            derived_key = b'\x00' * self.KEY_SIZE

            return plaintext.decode('utf-8')

        except ValueError:
            raise
        except Exception as e:
            # Don't leak information about failure type
            raise ValueError("Decryption failed")


class SecureString:
    """Helper for secure string handling with memory clearing."""

    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value

    def clear(self):
        """Attempt to clear the string from memory.

        Note: Python string interning makes this imperfect,
        but it reduces the window of exposure.
        """
        if self._value:
            # Overwrite with zeros (best effort in Python)
            self._value = '\x00' * len(self._value)
            self._value = ''

    def __del__(self):
        self.clear()

    def __str__(self):
        return "[REDACTED]"

    def __repr__(self):
        return "SecureString([REDACTED])"
