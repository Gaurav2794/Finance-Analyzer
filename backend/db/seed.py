"""
backend/db/seed.py
Development-only seed utility for testing and hackathon demo evaluation.
"""
from __future__ import annotations

import logging
from backend.auth.security import hash_password
from backend.db.database import SessionLocal
from backend.db.models import User
from backend.db.session import init_db

log = logging.getLogger("team3.seed")

DEMO_EMAIL = "demo@financeanalyzer.local"
DEMO_PASSWORD = "DemoPassword123!"
DEMO_NAME = "Demo Auditor"


def seed_demo_user() -> User:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=DEMO_NAME,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info("Created demo development user: %s", DEMO_EMAIL)
        return user
    finally:
        db.close()


if __name__ == "__main__":
    u = seed_demo_user()
    print(f"Demo user ready: id={u.id}, email={u.email}")
