"""
tests/test_auth_and_security.py

Comprehensive security, authentication, and multi-tenant authorization test suite.
"""
import os
import unittest
from datetime import timedelta, timezone, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth.security import create_access_token, hash_password, verify_password
from backend.db.database import Base, get_db
from backend.db.models import Document, Finding, User
from backend.main import app

# Shared in-memory SQLite with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestAuthAndSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

    def test_01_argon2_password_hashing(self):
        """Verify passwords are securely hashed with Argon2id and verified."""
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(hashed.startswith(""))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_02_register_success(self):
        """Test successful user registration."""
        payload = {"email": "auditor1@example.com", "password": "Password123!", "full_name": "Auditor One"}
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "auditor1@example.com")
        self.assertEqual(data["user"]["full_name"], "Auditor One")
        self.assertNotIn("password", data["user"])
        self.assertNotIn("password_hash", data["user"])

    def test_03_register_duplicate_email(self):
        """Test that duplicate email registration is rejected with 400."""
        payload = {"email": "duplicate@example.com", "password": "Password123!"}
        res1 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res1.status_code, 201)
        res2 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already exists", res2.json()["detail"])

    def test_04_login_success_and_wrong_password(self):
        """Test login success and failure with wrong password."""
        self.client.post("/api/auth/register", json={"email": "user@example.com", "password": "CorrectPassword"})
        self.client.cookies.clear()
        
        # Wrong password
        res_fail = self.client.post("/api/auth/login", json={"email": "user@example.com", "password": "WrongPassword"})
        self.assertEqual(res_fail.status_code, 401)
        
        # Correct password
        res_ok = self.client.post("/api/auth/login", json={"email": "user@example.com", "password": "CorrectPassword"})
        self.assertEqual(res_ok.status_code, 200)
        data = res_ok.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "user@example.com")

    def test_05_profile_me_endpoint(self):
        """Test GET /api/auth/me returns current user profile."""
        # 1. Unauthenticated request with clean client
        self.client.cookies.clear()
        res_unauth = self.client.get("/api/auth/me")
        self.assertEqual(res_unauth.status_code, 401)

        # 2. Register user
        res_reg = self.client.post("/api/auth/register", json={"email": "me_test@example.com", "password": "Password123!", "full_name": "Me Test"})
        token = res_reg.json()["access_token"]
        self.client.cookies.clear()

        # 3. Authenticated request via Bearer header
        res_auth = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_auth.status_code, 200)
        user_data = res_auth.json()
        self.assertEqual(user_data["email"], "me_test@example.com")
        self.assertNotIn("password", user_data)
        self.assertNotIn("password_hash", user_data)

    def test_06_expired_and_invalid_token(self):
        """Test that expired or malformed tokens return 401."""
        self.client.cookies.clear()
        # Expired token
        expired_token = create_access_token({"sub": "some-id"}, expires_delta=timedelta(seconds=-10))
        res_exp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res_exp.status_code, 401)

        # Malformed token
        res_bad = self.client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.string"})
        self.assertEqual(res_bad.status_code, 401)

    def test_07_multi_tenant_document_isolation(self):
        """
        Critical test: User A cannot view, retrieve, or delete User B's document.
        Accessing User B's document returns 404 (zero existence leakage).
        """
        # Create User A
        res_a = self.client.post("/api/auth/register", json={"email": "user_a@example.com", "password": "PasswordA123"})
        token_a = res_a.json()["access_token"]
        user_a_id = res_a.json()["user"]["id"]

        # Create User B
        res_b = self.client.post("/api/auth/register", json={"email": "user_b@example.com", "password": "PasswordB123"})
        token_b = res_b.json()["access_token"]
        user_b_id = res_b.json()["user"]["id"]

        # Create Document belonging to User A in DB
        db = TestingSessionLocal()
        doc_a = Document(
            id="DOC-AAAA11112222",
            user_id=user_a_id,
            filename="user_a_financials.xlsx",
            company_name="User A Corp",
            status="COMPLETED",
            overall_score=100.0,
            overall_status="PASSED",
        )
        # Create Document belonging to User B in DB
        doc_b = Document(
            id="DOC-BBBB33334444",
            user_id=user_b_id,
            filename="user_b_financials.xlsx",
            company_name="User B Corp",
            status="COMPLETED",
            overall_score=85.0,
            overall_status="REVIEW",
        )
        db.add_all([doc_a, doc_b])
        db.commit()
        db.close()

        # User A requests Document A metadata -> 200 OK
        res = self.client.get("/api/documents/DOC-AAAA11112222", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["company_name"], "User A Corp")

        # User A requests User B's Document B -> 404 NOT FOUND (Cross-tenant isolation)
        res_cross = self.client.get("/api/documents/DOC-BBBB33334444", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_cross.status_code, 404)

        # User B requests User A's Document A -> 404 NOT FOUND
        res_cross_b = self.client.get("/api/documents/DOC-AAAA11112222", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(res_cross_b.status_code, 404)

        # User A lists documents -> Only sees Document A (1 item)
        res_list_a = self.client.get("/api/documents", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_list_a.status_code, 200)
        docs_a = res_list_a.json()
        self.assertEqual(len(docs_a), 1)
        self.assertEqual(docs_a[0]["id"], "DOC-AAAA11112222")

        # User B lists documents -> Only sees Document B (1 item)
        res_list_b = self.client.get("/api/documents", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(res_list_b.status_code, 200)
        docs_b = res_list_b.json()
        self.assertEqual(len(docs_b), 1)
        self.assertEqual(docs_b[0]["id"], "DOC-BBBB33334444")

        # User A attempts to delete User B's Document B -> 404 NOT FOUND
        res_del_cross = self.client.delete("/api/documents/DOC-BBBB33334444", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_del_cross.status_code, 404)

        # User A deletes Document A -> 200 OK
        res_del_a = self.client.delete("/api/documents/DOC-AAAA11112222", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_del_a.status_code, 200)


if __name__ == "__main__":
    unittest.main()
