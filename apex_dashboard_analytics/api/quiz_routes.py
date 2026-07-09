"""Mirrors Team 4 contract 2.2: GET /api/v1/quizzes/{quiz_id}/attempts.

Lives outside /employees because that's the literal path Team 4
specified (attempts are looked up by quiz_id, not employee_id).
"""

from __future__ import annotations

from fastapi import HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_store
from apex_dashboard_analytics.schemas import QuizAttemptsResponse

quiz_router = APIRouter(prefix="/quizzes", tags=["quiz"])


@quiz_router.get("/{quiz_id}/attempts", response_model=QuizAttemptsResponse)
def get_quiz_attempts(
    quiz_id: str,
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
) -> QuizAttemptsResponse:
    """Mirrors Team 4 contract 2.2. Note: contract has no `search` param here."""
    result = mock_store.get_quiz_attempts(quiz_id, limit=limit, offset=offset)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found")
    return result