"""Schemas mirroring Team 3 (AI Tutor Agent) contract.

GET /api/v1/employees/{id}/asks
GET /api/v1/tutoring/{id}
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TutoringSession(BaseModel):
    employee_id: str
    session_id: str
    topics_covered: list[str]
    duration_minutes: int
    documents_accessed: list[str]
    timestamp: datetime


# --- Team 3 Analytics & Webhook Schemas ---
from typing import Literal
from pydantic import ConfigDict, Field


class UserAnalyticsSummary(BaseModel):
    user_id: str
    total_sessions: int
    total_messages: int
    total_questions_asked: int
    total_documents_uploaded: int
    avg_messages_per_session: float
    grounded_response_rate: float
    feedback_given: int
    thumbs_up_rate: float
    first_interaction: datetime
    last_interaction: datetime
    active_skills_count: int
    completed_skills_count: int


class UserSkillInteraction(BaseModel):
    skill_id: str
    skill_name: str
    skill_level: str
    target_role: str
    session_count: int
    total_messages: int
    total_questions: int
    documents_uploaded: int
    grounded_response_rate: float
    thumbs_up_rate: float
    last_interaction: datetime
    top_topics_asked: list[str]
    guardrail_blocks: int


class UserSkillsBreakdown(BaseModel):
    user_id: str
    skills: list[UserSkillInteraction]


class TutorOverviewPeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")


class TopSkillUsage(BaseModel):
    skill_name: str
    session_count: int


class TopUngroundedSkill(BaseModel):
    skill_name: str
    grounded_rate: float


class TutorOverviewResponse(BaseModel):
    period: TutorOverviewPeriod
    total_users: int
    active_users: int
    total_sessions: int
    total_messages: int
    avg_session_length_messages: int
    grounded_response_rate: float
    thumbs_up_rate: float
    documents_uploaded: int
    guardrail_block_rate: float
    top_skills: list[TopSkillUsage]
    top_ungrounded_skills: list[TopUngroundedSkill]


class QuizResultWebhookPayload(BaseModel):
    user_id: str
    skill_id: str
    quiz_id: str
    course: str
    score: int
    pass_threshold: int
    status: Literal["passed", "failed"]
    feedback: str
    weak_topics: list[str] = Field(default_factory=list)
    attempted_on: datetime