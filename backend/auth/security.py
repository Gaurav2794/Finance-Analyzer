"""
backend/auth/security.py
Security primitives: Argon2id password hashing and JWT access token creation/verification.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import datetime
import os
import secrets
from typing import Any, Dict, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash

# Password hasher configuration (Argon2id)
_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

# JWT Secret & Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "finance-analyzer-secret-key-change-in-production-" + secrets.token_hex(16))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its Argon2 hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generate a signed JWT access token with standard claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token. Returns payload dict or None if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
