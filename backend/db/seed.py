"""
backend/db/seed.py
Development-only seed utility for testing and hackathon demo evaluation.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.auth.security import hash_password
from backend.db.database import SessionLocal
from backend.db.models import User
from backend.db.session import init_db

log = logging.getLogger("team3.seed")

DEV_USERS = [
    ("auditor@example.com", "DemoPassword123!", "Auditor Lead"),
    ("demo@financeanalyzer.local", "DemoPassword123!", "Demo Auditor"),
]


def seed_demo_user() -> None:
    init_db()
    db = SessionLocal()
    try:
        for email, pwd, name in DEV_USERS:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=hash_password(pwd),
                    full_name=name,
                    is_active=True,
                )
                db.add(user)
                db.commit()
                log.info("Created dev seed user: %s", email)
    except Exception as exc:
        log.warning("Seed user creation notice: %s", exc)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_user()
    print("Development seed users verified in database.")
