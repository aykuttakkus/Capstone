import base64
import os
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Global SOTA: Clinical data should be encrypted with a key derived from 
# a system secret or user-specific entropy.
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "clinical-master-secret-change-in-prod")

def _get_fernet():
    # Deriving a stable key from the secret
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"psych-rag-salt",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
    return Fernet(key)

def encrypt_clinical_data(data: str) -> str:
    """Encrypts sensitive clinical nuggets before DB storage."""
    if not data: return ""
    f = _get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt_clinical_data(encrypted_data: str) -> str:
    """Decrypts clinical nuggets for AI context loading."""
    if not encrypted_data: return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return "[ENCRYPTION ERROR: Data integrity compromised]"


def redact_sensitive_text(text: str) -> str:
    """Redact obvious personal identifiers from debug/audit text."""
    if not text:
        return ""

    redacted = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[REDACTED_EMAIL]", text)
    redacted = re.sub(r"\b\+?\d[\d\s().-]{7,}\b", "[REDACTED_PHONE]", redacted)
    return redacted
