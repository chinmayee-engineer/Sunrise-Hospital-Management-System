"""Password hashing and lightweight session management.

Passwords are never stored in plain text (spec section 37). We use
PBKDF2-HMAC-SHA256 with a per-user random salt via the standard
library's hashlib -- no extra dependency required, and it's the
algorithm Django/many production systems used for years before
bcrypt/argon2 became easy to install everywhere.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass

PBKDF2_ITERATIONS = 200_000
SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes idle timeout


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Return (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return digest.hex(), salt.hex()


def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    digest, _ = hash_password(password, salt)
    return hmac.compare_digest(digest, password_hash)


@dataclass
class Session:
    user_id: str
    username: str
    full_name: str
    role_name: str
    linked_patient_id: str | None = None
    linked_doctor_id: str | None = None
    login_time: float = 0.0
    last_activity: float = 0.0

    def touch(self) -> None:
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > SESSION_TIMEOUT_SECONDS

    def has_permission(self, allowed_roles: tuple[str, ...]) -> bool:
        return self.role_name in allowed_roles or self.role_name == "Administrator"


_current_session: Session | None = None


def set_current_session(session: Session | None) -> None:
    global _current_session
    _current_session = session


def get_current_session() -> Session | None:
    return _current_session
