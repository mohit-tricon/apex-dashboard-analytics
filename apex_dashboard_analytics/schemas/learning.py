"""Schemas mirroring Team 2 (Learning Recommendation Agent) contract.

Source: API_Contract-Recommendation_of_courses.docx (2026-07-09) +
confirmed against Team 2's live Swagger docs (2026-07-09).

CONFIRMED endpoint (from Team 2's own /docs, operation id
`get_roadmaps_by_employee_api_v1_employees__employee_id__roadmap_get`):

    GET /api/v1/employees/{employee_id}/roadmap

This supersedes the doc's Overview table, which said `/{skill_id}/roadmap`
— that was wrong (and the doc's "Endpoint" section had a mismatched
display text/hyperlink on top of it, which was the first sign something
was off). Employee-id-scoped also matches how Team 4's quiz endpoints
are shaped, so this is consistent with the rest of the system.
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
    """Response shape for GET /employees/{employee_id}/roadmap."""

    roadmap_id: str
    skill_id: str
    target_role: str
    status: str
    plan: RoadmapPlan
    created_at: datetime