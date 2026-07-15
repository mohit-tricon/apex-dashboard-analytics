"""Schemas mirroring Team 4 (Assessment & Quiz Agent) contract.

Source: TEAM4-API-CONTRACT.docx, shared 2026-07-09. This one is clean
and internally consistent — matched exactly.

Endpoints covered:
    GET /api/v1/employees/{employee_id}/quizzes        (2.1 - overview)
    GET /api/v1/quizzes/{quiz_id}/attempts              (2.2 - single quiz)
    GET /api/v1/employees/{employee_id}/quiz-attempts   (2.3 - cross-quiz)

All three are paginated (`limit`/`offset`) and support `search`
(2.2 does not support search per the doc's note).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from apex_dashboard_analytics.constants import FAILED, IN_PROGRESS, NOT_STARTED, PASSED

QuizStatus = Literal[PASSED, FAILED, IN_PROGRESS, NOT_STARTED]
AttemptStatus = Literal[PASSED, FAILED]


class Pagination(BaseModel):
    limit: int = 20
    offset: int = 0
    total: int
    has_more: bool


# ---------------------------------------------------- 2.1 Employee quizzes


class QuizSummary(BaseModel):
    quiz_id: str
    skill_id: str
    course: str
    last_score: int | None = Field(default=None, ge=0, le=100)
    pass_threshold: int = Field(ge=0, le=100)
    status: QuizStatus


class EmployeeQuizzesResponse(BaseModel):
    employee_id: str
    quizzes: list[QuizSummary]
    pagination: Pagination


# ----------------------------------------------------- 2.2 Single-quiz attempts


class QuizAttempt(BaseModel):
    course: str
    score: int | None = Field(default=None, ge=0, le=100)
    status: AttemptStatus
    attempted_on: datetime | None = None
    feedback: str | None = None


class QuizAttemptsResponse(BaseModel):
    employee_id: str
    quiz_id: str
    attempts: list[QuizAttempt]
    pagination: Pagination


# ------------------------------------------------ 2.3 Cross-quiz attempts


class EmployeeQuizAttempt(BaseModel):
    quiz_id: str
    skill_id: str
    course: str
    score: int | None = Field(default=None, ge=0, le=100)
    status: AttemptStatus
    attempted_on: datetime | None = None
    feedback: str | None = None


class EmployeeQuizAttemptsResponse(BaseModel):
    employee_id: str
    attempts: list[EmployeeQuizAttempt]
    pagination: Pagination