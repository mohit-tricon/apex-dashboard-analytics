"""Mirrors assessment contract 2.2: GET /api/v1/quizzes/{quiz_id}/attempts.

Lives outside /employees because that's the literal path the assessment
service specified (attempts are looked up by quiz_id, not employee_id).

``quiz_id`` maps to assessment service ``course_id``. The employee context is
resolved from the ``X-Employee-Id`` header set by the API gateway.
"""

from __future__ import annotations

from fastapi import Depends, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.api.deps import get_scoped_employee_id
from apex_dashboard_analytics.schemas import QuizAttemptsResponse
from apex_dashboard_analytics.services.assessment_service import get_assessment_service

quiz_router = APIRouter(prefix="/quizzes", tags=["quiz"])


@quiz_router.get("/{quiz_id}/attempts", response_model=QuizAttemptsResponse)
def get_quiz_attempts(
    quiz_id: str,
    employee_id: str = Depends(get_scoped_employee_id),
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
) -> QuizAttemptsResponse:
    """Mirrors assessment contract 2.2. Note: contract has no `search` param here."""
    return get_assessment_service().get_quiz_attempts(
        quiz_id, employee_id, limit=limit, offset=offset
    )
