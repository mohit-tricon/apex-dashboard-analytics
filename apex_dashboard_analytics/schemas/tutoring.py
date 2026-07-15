"""Schemas mirroring Team 3 (AI Tutor Agent) contract.

Source: Team_3_-_API_Contract__Cross-team_dependencies_.pdf, shared
2026-07-09 (sections 3 & 4: cross-team dependencies).

Team 5 only CONSUMES the read-only analytics endpoints below (§4).
The quiz-result webhook (§3, POST /tutor/hooks/quiz-result) is a
Team 4 -> Team 3 integration; we don't call or host it, so it's not
wired into any router — the schema is kept here for reference only.

Confirmed endpoints (note: no /api/v1 prefix — unlike every other
team's contract, Team 3's paths are literally /tutor/...):

    GET /tutor/analytics/user/{user_id}/summary
    GET /tutor/analytics/user/{user_id}/skills
    GET /tutor/analytics/overview

Naming note: the JSON payloads Team 3 sends use `user_id` (that's
their DB column name, and matches Team 3's own flagged gap: they're
not 100% sure `employee_id` from Team 4's contract maps 1:1 to their
`users.user_id`). Model *class* names below use "Employee" to match
this project's convention (EmployeeDashboard, EmployeeQuizzesResponse,
etc.) — the `user_id` *field* stays as-is since that's the literal
wire format Team 3 sends. Don't rename the field without confirming
with Team 3 first.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from apex_dashboard_analytics.constants import FAILED, PASSED

# --------------------------------------------------- §4.1 engagement summary


class EmployeeAnalyticsSummary(BaseModel):
    """GET /tutor/analytics/user/{user_id}/summary"""

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


# ------------------------------------------------- §4.2 per-skill breakdown


class EmployeeSkillInteraction(BaseModel):
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
    top_topics_asked: list[str] = Field(default_factory=list)
    guardrail_blocks: int


class EmployeeSkillAnalytics(BaseModel):
    """GET /tutor/analytics/user/{user_id}/skills"""

    user_id: str
    skills: list[EmployeeSkillInteraction]


# ------------------------------------------------- §4.3 platform overview


class TutorAnalyticsPeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: date = Field(alias="from")
    to: date


class TopSkillBySessionCount(BaseModel):
    skill_name: str
    session_count: int


class TopUngroundedSkill(BaseModel):
    skill_name: str
    grounded_rate: float


class TutorAnalyticsOverview(BaseModel):
    """GET /tutor/analytics/overview?from=&to="""

    period: TutorAnalyticsPeriod
    total_users: int
    active_users: int
    total_sessions: int
    total_messages: int
    avg_session_length_messages: float
    grounded_response_rate: float
    thumbs_up_rate: float
    documents_uploaded: int
    guardrail_block_rate: float
    top_skills: list[TopSkillBySessionCount]
    top_ungrounded_skills: list[TopUngroundedSkill]


# --------------------------------------------------------------------------
# §3 reference only — Team 4 -> Team 3 webhook. NOT called or hosted by
# Team 5. Kept here purely so the payload shape is documented in one place.
# --------------------------------------------------------------------------


class QuizResultWebhookPayload(BaseModel):
    """POST /tutor/hooks/quiz-result (Team 4 -> Team 3, reference only).

    Known gap per Team 3's doc: `weak_topics` is not currently part of
    Team 4's own contract — Team 3 is asking Team 4 to add it.
    """

    user_id: str
    skill_id: str
    quiz_id: str
    course: str
    score: int = Field(ge=0, le=100)
    pass_threshold: int = Field(ge=0, le=100)
    status: Literal[PASSED, FAILED]
    feedback: str
    weak_topics: list[str] = Field(default_factory=list)
    attempted_on: datetime