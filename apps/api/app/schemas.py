"""API request/response schemas (DTOs)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.adapters.models import RoadmapItemStatus, SkillCategory, SkillSource, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Profile / Skills ----
class ProfileUpdate(BaseModel):
    education: list[Any] | None = None
    learning_style: str | None = Field(default=None, max_length=50)
    weekly_hours: int | None = Field(default=None, ge=0, le=168)
    target_companies: list[str] | None = None
    expected_salary: int | None = Field(default=None, ge=0)
    interests: list[str] | None = None
    career_goal: str | None = Field(default=None, max_length=200)


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    education: list[Any] | None
    learning_style: str | None
    weekly_hours: int | None
    target_companies: list[str] | None
    expected_salary: int | None
    interests: list[str] | None
    career_goal: str | None
    twin_version: int

    model_config = {"from_attributes": True}


class SkillOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: SkillCategory

    model_config = {"from_attributes": True}


class UserSkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=120)
    proficiency: int = Field(default=0, ge=0, le=100)
    source: SkillSource = SkillSource.manual


class UserSkillOut(BaseModel):
    skill_id: uuid.UUID
    name: str
    slug: str
    category: SkillCategory
    proficiency: int
    source: SkillSource

    model_config = {"from_attributes": True}


# ---- Onboarding / Readiness ----
class OnboardingSkill(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    proficiency: int = Field(default=50, ge=0, le=100)


class OnboardingRequest(BaseModel):
    education: list[Any] | None = None
    learning_style: str | None = Field(default=None, max_length=50)
    weekly_hours: int | None = Field(default=None, ge=0, le=168)
    target_companies: list[str] | None = None
    expected_salary: int | None = Field(default=None, ge=0)
    interests: list[str] | None = None
    career_goal: str | None = Field(default=None, max_length=200)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    skills: list[OnboardingSkill] = Field(default_factory=list)
    github_username: str | None = Field(default=None, max_length=100)


class ReadinessOut(BaseModel):
    overall: int
    components: dict[str, Any]
    target_role_slug: str | None
    computed_at: datetime

    model_config = {"from_attributes": True}


class OnboardingResultOut(BaseModel):
    profile_id: uuid.UUID
    readiness: ReadinessOut
    added_skills: list[str]
    skipped_skills: list[str]


# ---- Chat ----
class ChatAsk(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class CitationOut(BaseModel):
    title: str
    source: str
    url: str | None
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    intent: str
    target_role: str | None
    citations: list[CitationOut]


# ---- Conversations ----
class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessage(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


# ---- Gap analysis / Roadmap ----
class TargetRoleRequest(BaseModel):
    target_role: str | None = None


class SkillGapOut(BaseModel):
    skill_slug: str
    skill_name: str
    importance: int
    current: int
    target: int
    gap: int
    difficulty: int
    est_hours: int
    confidence: float
    order_index: int
    explanation: dict[str, Any]


class RoadmapItemOut(BaseModel):
    id: uuid.UUID
    skill_name: str
    order_index: int
    milestone: int
    est_hours: int
    difficulty: int
    importance: int
    status: RoadmapItemStatus
    explanation: dict[str, Any]

    model_config = {"from_attributes": True}


class RoadmapOut(BaseModel):
    id: uuid.UUID
    target_role_slug: str
    target_role_name: str
    version: int
    status: str
    rationale: dict[str, Any]
    items: list[RoadmapItemOut]

    model_config = {"from_attributes": True}


class RoadmapVersionOut(BaseModel):
    id: uuid.UUID
    target_role_name: str
    version: int
    status: str

    model_config = {"from_attributes": True}


class ItemStatusUpdate(BaseModel):
    status: RoadmapItemStatus


# ---- Resume ----
class ResumeScoreOut(BaseModel):
    ats_score: int
    sections: dict[str, bool]
    missing_keywords: list[str]
    detected_skills: list[str]

    model_config = {"from_attributes": True}


class ResumeUploadOut(BaseModel):
    resume_id: uuid.UUID
    filename: str
    ats_score: int
    detected_skills: list[str]
    missing_keywords: list[str]


class ResumeDetailOut(BaseModel):
    id: uuid.UUID
    filename: str
    text_excerpt: str
    score: ResumeScoreOut | None


class ResumeRewriteOut(BaseModel):
    improved_bullets: list[str]
    keyword_suggestions: list[str]
    summary_feedback: str


# ---- GitHub ----
class GithubAnalyzeRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)


class GithubOut(BaseModel):
    username: str
    name: str | None
    bio: str | None
    followers: int
    public_repos: int
    repo_score: int
    diversity_score: int
    health_score: int
    recruiter_score: int
    languages: list[str]
    top_repos: list[dict[str, Any]]
    summary: str | None

    model_config = {"from_attributes": True}
