"""
backend/auth/dependencies.py
FastAPI route dependencies for authentication, token extraction,
and per-document ownership authorization.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.auth.security import decode_access_token
from backend.db.database import get_db
from backend.db.models import Document, User

log = logging.getLogger("team3.auth")
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts Bearer token from Authorization header or cookie.
    Validates token claims and returns the authenticated User record.
    Raises 401 UNAUTHORIZED if token is missing, invalid, or user does not exist.
    """
    token: Optional[str] = None
    if auth_creds:
        token = auth_creds.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Bearer token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def get_optional_user(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional user extraction without raising 401 if missing."""
    try:
        return await get_current_user(request, auth_creds, db)
    except HTTPException:
        return None


def get_user_document(
    document_id: str,
    db: Session,
    current_user: User,
) -> Document:
    """
    Enforces document ownership.
    Queries the database for Document where id == document_id AND user_id == current_user.id.
    Raises 404 NOT FOUND if document does not exist OR belongs to another user.
    (404 is preferred to avoid leaking document existence to unauthorized users).
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not doc:
        log.warning("Access denied or not found: doc=%s, user=%s", document_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    return doc
