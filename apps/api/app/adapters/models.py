"""ORM models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class AuthProvider(str, enum.Enum):
    password = "password"
    github = "github"
    google = "google"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, native_enum=False, length=20),
        default=AuthProvider.password,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        default=UserRole.user,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SkillCategory(str, enum.Enum):
    language = "language"
    framework = "framework"
    library = "library"
    db = "db"
    tool = "tool"
    cloud = "cloud"
    ai = "ai"
    soft = "soft"
    cert = "cert"


class SkillSource(str, enum.Enum):
    resume = "resume"
    github = "github"
    linkedin = "linkedin"
    chat = "chat"
    manual = "manual"


class Profile(Base):
    """The Career Twin core (1:1 with a user)."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    education: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    learning_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weekly_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_companies: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    expected_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interests: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    career_goal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    twin_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class Skill(Base):
    """Canonical skill taxonomy entry."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    category: Mapped[SkillCategory] = mapped_column(
        Enum(SkillCategory, native_enum=False, length=20), nullable=False
    )
    aliases: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    esco_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    onet_id: Mapped[str | None] = mapped_column(String(60), nullable=True)


class UserSkill(Base):
    """A skill edge on a profile, with evidence and provenance."""

    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("profile_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    proficiency: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0-100
    source: Mapped[SkillSource] = mapped_column(
        Enum(SkillSource, native_enum=False, length=20), default=SkillSource.manual
    )
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Role(Base):
    """A target career role."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)


class RoleSkillRequirement(Base):
    """Skill requirement for a role (used by gap analysis)."""

    __tablename__ = "role_skill_requirements"
    __table_args__ = (UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    importance: Mapped[int] = mapped_column(SmallInteger, default=50)  # 0-100
    typical_proficiency: Mapped[int] = mapped_column(SmallInteger, default=60)  # 0-100
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=50)  # 0-100


class ReadinessScore(Base):
    """A computed Career Readiness snapshot (weighted, explainable components)."""

    __tablename__ = "readiness_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0-100
    components: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    target_role_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RoadmapItemStatus(str, enum.Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    skipped = "skipped"


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_role_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    target_role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    rationale: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    milestone: Mapped[int] = mapped_column(Integer, default=1)
    est_hours: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=50)
    importance: Mapped[int] = mapped_column(SmallInteger, default=50)
    status: Mapped[RoadmapItemStatus] = mapped_column(
        Enum(RoadmapItemStatus, native_enum=False, length=20),
        default=RoadmapItemStatus.todo,
    )
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    resources: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_key: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ResumeScore(Base):
    __tablename__ = "resume_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ats_score: Mapped[int] = mapped_column(SmallInteger, default=0)
    sections: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    missing_keywords: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    detected_skills: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    suggestions: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=20), nullable=False
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    citations: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    agent_trace: Mapped[list[Any] | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
