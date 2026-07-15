"""Internal Pydantic models for assessment service responses.

These mirror the upstream API contract and are not exposed on the
frontend-facing dashboard routes. The mapper layer translates them into
``schemas.quiz`` models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from apex_dashboard_analytics.constants import FAIL, PASS, PENDING

AssessmentResultStatus = Literal[PASS, FAIL, PENDING]


class AssessmentPagination(BaseModel):
    limit: int = 20
    offset: int = 0
    total: int
    has_more: bool


class AssessmentRecord(BaseModel):
    assessment_id: str
    course_id: str
    course: str
    last_score: int | None = Field(default=None, ge=0, le=100)
    pass_threshold: int = Field(ge=0, le=100)
    status: AssessmentResultStatus


class EmployeeAssessmentsResponse(BaseModel):
    user_id: str
    assessments: list[AssessmentRecord]
    pagination: AssessmentPagination


class AssessmentAttemptRecord(BaseModel):
    assessment_id: str
    course_id: str
    course: str
    score: int | None = Field(default=None, ge=0, le=100)
    status: AssessmentResultStatus
    attempted_on: datetime | None = None
    feedback: str | None = None


class EmployeeAssessmentAttemptsResponse(BaseModel):
    user_id: str
    attempts: list[AssessmentAttemptRecord]
    pagination: AssessmentPagination


class CourseAssessmentAttempt(BaseModel):
    user_id: str
    assessment_id: str
    score: int | None = Field(default=None, ge=0, le=100)
    status: AssessmentResultStatus
    attempted_on: datetime | None = None


class CourseAssessmentAttemptsResponse(BaseModel):
    course_id: str
    attempts: list[CourseAssessmentAttempt]
    pagination: AssessmentPagination
