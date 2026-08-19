"""
backend/db/models.py
SQLAlchemy ORM models for Users, Documents, Findings, and AI Interactions.
Provides persistence and audit history metadata without modifying or replacing
the authoritative Segment 1 and Segment 2 review engines.
"""
from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


def _gen_uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_gen_uuid_str, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)  # e.g., DOC-1234567890AB
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    current_period = Column(String(64), nullable=True)
    previous_period = Column(String(64), nullable=True)
    currency = Column(String(16), default="INR", nullable=True)
    scale = Column(String(32), default="Millions", nullable=True)
    status = Column(String(32), default="UPLOADED", nullable=False)  # UPLOADED, EXTRACTING, EXTRACTED, REVIEWING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    upload_path = Column(String(512), nullable=True)
    financial_data_path = Column(String(512), nullable=True)
    review_result_path = Column(String(512), nullable=True)
    overall_score = Column(Float, nullable=True)
    overall_status = Column(String(32), nullable=True)  # EXCELLENT, ATTENTION_REQUIRED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="documents")
    findings = relationship("Finding", back_populates="document", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} user_id={self.user_id} filename={self.filename} status={self.status}>"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(64), nullable=False, index=True)  # e.g., MA-01, RD-01
    category = Column(String(64), nullable=False)
    check_name = Column(String(255), nullable=False)
    severity = Column(String(32), nullable=False)  # CRITICAL, HIGH, REVIEW, PASSED
    status = Column(String(32), nullable=True)  # PASSED, WARNING, FAILED, NOT_AVAILABLE
    description = Column(Text, nullable=True)
    expected_value = Column(String(128), nullable=True)
    actual_value = Column(String(128), nullable=True)
    difference = Column(String(128), nullable=True)
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="findings")

    __table_args__ = (
        Index("ix_findings_doc_category", "document_id", "category"),
    )

    def __repr__(self) -> str:
        return f"<Finding id={self.id} doc={self.document_id} fid={self.finding_id} sev={self.severity}>"


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(64), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(64), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    model = Column(String(64), nullable=True)
    grounded = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="ai_interactions")
    document = relationship("Document", back_populates="ai_interactions")

    def __repr__(self) -> str:
        return f"<AIInteraction id={self.id} doc={self.document_id} user={self.user_id}>"
