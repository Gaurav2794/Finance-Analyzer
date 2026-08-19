"""
backend/routes/auth.py
Authentication endpoints: Registration, Login, Profile (/me), and Logout.
"""
from __future__ import annotations

import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.db.database import get_db
from backend.db.models import User

router = APIRouter()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format.")
        return v


class UserLoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Register a new user account with email and password.
    Validates unique email and password requirements.
    Never returns password or password_hash.
    """
    email_clean = body.email

    # Check if user already exists
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Validate password length/strength
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters long.",
        )

    # Create new user with Argon2id hash
    hashed = hash_password(body.password)
    user = User(
        email=email_clean,
        password_hash=hashed,
        full_name=body.full_name.strip() if body.full_name else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token({"sub": user.id, "email": user.email})

    # Set HTTP-only cookie for secure browser environments
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password.
    Returns signed JWT access token and user profile.
    """
    email_clean = body.email
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    token = create_access_token({"sub": user.id, "email": user.email})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve the profile of the currently authenticated user.
    Never returns password or password_hash.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(response: Response):
    """
    Logout current user session by clearing auth cookie.
    """
    response.delete_cookie(key="access_token")
    return {"status": "ok", "message": "Successfully logged out."}
