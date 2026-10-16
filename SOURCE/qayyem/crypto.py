"""Encryption for instructor-supplied API keys.

An instructor's API key is their own credential, and it is billable, so storing
it as plain text in the database would be careless even for a local deployment.
Keys are encrypted with Fernet (AES-128-CBC with an HMAC), using a key derived
from the application's SECRET_KEY.

The honest limit of this: the encryption key is derived from SECRET_KEY, which
lives in .env next to the database. Anyone who can read both can decrypt. This
protects against casual disclosure -- a database file copied to a USB stick, an
accidental commit, a screenshot of a table -- not against an attacker who has
already taken the whole application directory. Real key management belongs in a
secrets manager, which is out of scope for this project.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _fernet(secret_key):
    """Derive a Fernet key from the application secret."""
    if not secret_key:
        raise ValueError("SECRET_KEY must be set before encrypting API keys.")
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_key(secret_key, plaintext):
    """Encrypt an API key for storage. Returns None for an empty key."""
    if not plaintext:
        return None
    return _fernet(secret_key).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_key(secret_key, ciphertext):
    """Decrypt a stored API key.

    Returns None when there is nothing stored, or when the stored value cannot
    be decrypted -- which happens if SECRET_KEY changed after the key was saved.
    Returning None rather than raising lets the caller fall back to the server's
    own key and tell the instructor to re-enter theirs.
    """
    if not ciphertext:
        return None
    try:
        return _fernet(secret_key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def mask_key(plaintext):
    """Render a key for display without revealing it.

    The interface never sends a stored key back to the browser; it shows this
    instead, which is enough for an instructor to recognise which key is saved.
    """
    if not plaintext:
        return ""
    if len(plaintext) <= 8:
        return "*" * len(plaintext)
    return plaintext[:3] + "*" * 8 + plaintext[-4:]
