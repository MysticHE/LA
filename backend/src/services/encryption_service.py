"""Encryption service for secure API key storage using AES-256.

This module provides AES-256-GCM encryption for API keys to ensure
they are securely stored at rest.
"""

import os
import base64
import secrets
from typing import Optional


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using AES-256-GCM.

    Uses the cryptography library for secure AES-256 encryption with
    authenticated encryption (GCM mode) to prevent tampering.

    Attributes:
        _key: The 256-bit encryption key (32 bytes).
    """

    # AES-256 requires 32-byte key
    KEY_SIZE = 32
    # GCM nonce size (96 bits recommended by NIST)
    NONCE_SIZE = 12
    # GCM tag size
    TAG_SIZE = 16

    def __init__(self, key: Optional[bytes] = None):
        """Initialize the encryption service.

        Args:
            key: Optional 32-byte encryption key. If not provided,
                 attempts to load from ENCRYPTION_KEY environment variable,
                 or generates a new key.
        """
        if key is not None:
            if len(key) != self.KEY_SIZE:
                raise ValueError(f"Key must be {self.KEY_SIZE} bytes for AES-256")
            self._key = key
        else:
            self._key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        """Load encryption key from environment or generate a new one.

        Returns:
            32-byte encryption key.
        """
        env_key = os.environ.get("ENCRYPTION_KEY")
        if env_key:
            try:
                key = base64.b64decode(env_key)
                if len(key) == self.KEY_SIZE:
                    return key
            except Exception:
                pass

        # Generate a new key if not found or invalid
        return secrets.token_bytes(self.KEY_SIZE)

    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new random AES-256 key.

        Returns:
            32 bytes of cryptographically secure random data.
        """
        return secrets.token_bytes(cls.KEY_SIZE)

    @classmethod
    def key_to_base64(cls, key: bytes) -> str:
        """Convert a key to base64 string for storage.

        Args:
            key: The encryption key bytes.

        Returns:
            Base64-encoded string representation of the key.
        """
        return base64.b64encode(key).decode('utf-8')

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string using AES-256-GCM.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded string containing nonce + ciphertext + tag.

        Raises:
            ValueError: If plaintext is empty.
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        # Generate a random nonce for each encryption
        nonce = secrets.token_bytes(self.NONCE_SIZE)

        # Create cipher and encrypt
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        # Combine nonce + ciphertext (tag is appended by AESGCM)
        combined = nonce + ciphertext

        # Return as base64 for easy storage
        return base64.b64encode(combined).decode('utf-8')

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an AES-256-GCM encrypted string.

        Args:
            encrypted_data: Base64-encoded string from encrypt().

        Returns:
            The original plaintext string.

        Raises:
            ValueError: If encrypted_data is empty or invalid.
            InvalidTag: If the data has been tampered with.
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty string")

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        try:
            # Decode from base64
            combined = base64.b64decode(encrypted_data)

            # Split nonce and ciphertext
            nonce = combined[:self.NONCE_SIZE]
            ciphertext = combined[self.NONCE_SIZE:]

            # Create cipher and decrypt
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext.decode('utf-8')

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
