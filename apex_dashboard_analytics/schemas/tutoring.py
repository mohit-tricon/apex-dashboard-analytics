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