"""Schemas mirroring Team 2 (Learning Recommendation Agent) contract.

Source: API_Contract-Recommendation_of_courses.docx, shared 2026-07-09.

Canonical endpoint (per the doc's Overview table):
    GET /api/v1/{skill_id}/roadmap

NOTE: the same doc's "Endpoint" section shows a different, inconsistent
URL (display text vs. hyperlink target don't match — looks like a
copy-paste leftover pointing at an old design). Going with the Overview
table's `/{skill_id}/roadmap` as canonical; flag this doc inconsistency
with Team 2 so they can confirm/fix it.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RoadmapCourse(BaseModel):
    course_id: str
    course_name: str
    provider: str
    url: str
    duration_hours: float | None = None
    skills_taught: list[str] = Field(default_factory=list)


class RoadmapWeek(BaseModel):
    week: int
    focus: str
    skills: list[str] = Field(default_factory=list)
    courses: list[RoadmapCourse] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)


class RoadmapPlan(BaseModel):
    summary: str
    total_weeks: int
    weeks: list[RoadmapWeek] = Field(default_factory=list)


class Roadmap(BaseModel):
    """Response shape for GET /{skill_id}/roadmap."""

    roadmap_id: str
    skill_id: str
    target_role: str
    status: str
    plan: RoadmapPlan
    created_at: datetime