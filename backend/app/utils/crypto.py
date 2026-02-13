"""Encryption utilities for sensitive data."""

import os
from cryptography.fernet import Fernet
from typing import Optional
import base64
from pathlib import Path

# Default encryption key file location
KEY_FILE = Path("secret.key")


def get_or_create_key() -> bytes:
    """
    Get existing encryption key or create a new one.
    
    Returns:
        bytes: Fernet encryption key
    """
    if KEY_FILE.exists():
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        # Generate new key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key


def encrypt_string(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt a plaintext string.
    
    Args:
        plaintext: String to encrypt (can be None)
        
    Returns:
        str: Base64-encoded encrypted string, or None if input is None
    """
    if plaintext is None or plaintext == "":
        return None
    
    key = get_or_create_key()
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_string(encrypted: Optional[str]) -> Optional[str]:
    """
    Decrypt an encrypted string.
    
    Args:
        encrypted: Base64-encoded encrypted string (can be None)
        
    Returns:
        str: Decrypted plaintext string, or None if input is None
    """
    if encrypted is None or encrypted == "":
        return None
    
    try:
        key = get_or_create_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted.encode())
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, might be unencrypted legacy data
        # Return as-is (this is a safety fallback)
        return encrypted
