"""Schemas mirroring Team 1 (Employee Skill Profiler Agent) contract.

Source of truth: Team 1's actual FastAPI router (skill_analysis router,
`SkillDetailResponse`), shared 2026-07-09. Field names are camelCase
because that's what Team 1 ships.

Real Team 1 endpoints (for reference — NOT proxied 1:1 by this service
yet, see note below):
    POST   /api/v1/skill-analysis
    GET    /api/v1/skill-analysis            (caller's own assessments)
    GET    /api/v1/skill-analysis/{skill_id} (owner only)
    DELETE /api/v1/skill-analysis/{skill_id} (owner only)

IMPORTANT INTEGRATION GAP: Team 1's GET endpoints are scoped to the
caller's own bearer-token identity (`get_current_user`) — there is no
`employee_id` path param, and a manager requesting someone else's
`skill_id` gets a 403. Team 5's Manager/Executive views need
cross-employee visibility, which this contract does not currently
support. Raise this with Team 1 (they either need a manager-scoped
endpoint, or Team 5 needs direct DB/service-role read access).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SkillGapItem(BaseModel):
    skill: str
    requiredLevel: int = 0


class SkillDetailResponse(BaseModel):
    """Mirrors Team 1's `SkillDetailResponse` exactly."""

    skillId: str
    userId: str
    username: str | None = None
    email: str | None = None
    currentRole: str
    targetRole: str
    skills: dict[str, Any] = Field(default_factory=dict)
    skillGaps: list[SkillGapItem] = Field(default_factory=list)
    roleAlignment: str = "ALIGNED"
    resumePath: str | None = None
    status: str = "COMPLETED"
    createdAt: datetime
    llmProvider: str | None = None
    llmModel: str | None = None