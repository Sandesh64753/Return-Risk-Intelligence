import hmac
import hashlib
import secrets
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings

# Initialize Argon2 password hasher with recommended modern parameters
_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1)

# Serializer for signed, tamper-proof session cookies
_serializer = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY, salt="company-session-salt")
_csrf_serializer = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY, salt="csrf-salt")


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        return False


def create_session_token(company_id: int) -> str:
    """Generate a signed session token encoding the company identifier."""
    return _serializer.dumps({"cid": company_id, "nonce": secrets.token_hex(8)})


def decode_session_token(token: str, max_age: Optional[int] = None) -> Optional[int]:
    """Decode and verify a session token, returning the company_id or None if invalid/expired."""
    if not token:
        return None
    age = max_age if max_age is not None else settings.SESSION_MAX_AGE_SECONDS
    try:
        data = _serializer.loads(token, max_age=age)
        return data.get("cid")
    except (BadSignature, SignatureExpired):
        return None
    except Exception:
        return None


def generate_csrf_token(session_token: str) -> str:
    """Generate a CSRF token bound to the current session."""
    if not session_token:
        # Fallback for anonymous state-changing forms (like registration/login)
        return _csrf_serializer.dumps({"anon": True, "token": secrets.token_hex(16)})
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        session_token.encode(),
        hashlib.sha256
    ).hexdigest()
    return _csrf_serializer.dumps({"session_digest": digest})


def verify_csrf_token(session_token: str, submitted_token: str) -> bool:
    """Verify that the submitted CSRF token matches the session or anonymous form."""
    if not submitted_token:
        return False
    try:
        data = _csrf_serializer.loads(submitted_token, max_age=3600 * 4)  # 4 hour form validity
        if "anon" in data:
            return True
        expected_digest = hmac.new(
            settings.SECRET_KEY.encode(),
            (session_token or "").encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(data.get("session_digest", ""), expected_digest)
    except (BadSignature, SignatureExpired):
        return False
    except Exception:
        return False
