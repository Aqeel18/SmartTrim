"""
Database models — SmartTrim 360 Phase 3.

Uses SQLAlchemy 2.x with a declarative base.

Switching backends:
  - Development:  SQLite  (DATABASE_URL=sqlite:///./smarttrim.db)
  - Production:   PostgreSQL (DATABASE_URL=postgresql+asyncpg://user:pass@host/db)

The models cover:
  User          — authenticated account with profile preferences
  Generation    — every hairstyle preview a user generates (immutable audit log)
  FaceProfile   — cached face shape result per user (avoids re-running analysis)
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def _uuid():
    return str(uuid.uuid4())


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id           = Column(String(36), primary_key=True, default=_uuid)
    email        = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(120), nullable=True)
    hashed_pw    = Column(String(255), nullable=False)
    is_active    = Column(Boolean, default=True, nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    generations  = relationship("Generation",  back_populates="user", cascade="all, delete-orphan")
    face_profile = relationship("FaceProfile", back_populates="user", uselist=False,
                                cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id!r} email={self.email!r}>"


# ─── FaceProfile ──────────────────────────────────────────────────────────────

class FaceProfile(Base):
    """
    Cached face analysis result for a user.
    Avoids re-running MediaPipe + classifier on every visit.
    Invalidated when the user uploads a new photo.
    """
    __tablename__ = "face_profiles"

    id           = Column(String(36), primary_key=True, default=_uuid)
    user_id      = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    face_shape   = Column(String(32),  nullable=False)       # e.g. 'Oval'
    confidence   = Column(Float,       nullable=True)        # 0.0 – 1.0
    method       = Column(String(16),  nullable=True)        # 'ml' or 'geometric'

    # Raw metrics JSON — stored as text, parsed on read
    metrics_json = Column(Text, nullable=True)

    # Head pose
    yaw          = Column(Float, nullable=True)
    pitch        = Column(Float, nullable=True)
    roll         = Column(Float, nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="face_profile")

    def __repr__(self):
        return f"<FaceProfile user={self.user_id!r} shape={self.face_shape!r}>"


# ─── Generation ───────────────────────────────────────────────────────────────

class Generation(Base):
    """
    Immutable record of a single hairstyle generation.

    result_url references a cloud storage path (S3/R2) or a local path.
    In development, we store the path under uploads/; in production it
    should be an S3 pre-signed URL or a CDN path.
    """
    __tablename__ = "generations"

    id           = Column(String(36), primary_key=True, default=_uuid)
    user_id      = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    hairstyle    = Column(String(255), nullable=False)       # style value string
    style_name   = Column(String(255), nullable=True)        # human-readable
    face_shape   = Column(String(32),  nullable=True)        # face shape at time of generation

    # Storage
    result_url   = Column(Text, nullable=True)               # URL or path to JPEG
    input_hash   = Column(String(64), nullable=True)         # SHA256 of input image (dedup)

    # Pipeline metadata
    pipeline     = Column(String(32), nullable=True)         # 'diffusion' | 'template'
    duration_ms  = Column(Integer,    nullable=True)         # wall-clock inference time

    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="generations")

    def __repr__(self):
        return f"<Generation id={self.id!r} style={self.hairstyle!r}>"
