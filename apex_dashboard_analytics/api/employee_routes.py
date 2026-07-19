"""Employee View endpoints.

Two kinds of routes here:
  1. Team 5's own aggregated `/dashboard` endpoint (our design).
  2. Endpoints that mirror the other teams' real contracts.

Confirmed against real contracts as of 2026-07-09:
  - Assessment (quizzes, quiz-attempts): matched exactly against their doc.
  - Team 2 (roadmap): matched exactly against their live Swagger docs
    (GET /api/v1/employees/{employee_id}/roadmap).

NOT yet confirmed:
  - Team 1 (current-skills): their real `GET /api/v1/skill-analysis` is
    scoped to the caller's own bearer token, not an `employee_id` path
    param, so `/employees/{employee_id}/current-skills` below is shaped
    like their response (`SkillDetailResponse`) but is not a literal
    proxy — the real integration needs either a manager-scoped endpoint
    from Team 1 or direct DB access. Flagged for follow-up.
  - Team 3 (AI Tutor): analytics are wired up separately under
    /tutor/analytics — see tutor_routes.py.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.api.deps import use_mock_data
from apex_dashboard_analytics.data import mock_data, mock_json
from apex_dashboard_analytics.schemas import (
    EmployeeDashboard,
    EmployeeQuizAttemptsResponse,
    EmployeeQuizzesResponse,
    SkillDetailResponse,
)
from apex_dashboard_analytics.services.assessment_service import get_assessment_service
from apex_dashboard_analytics.schemas.learning import Roadmap
from apex_dashboard_analytics.integrations.learning_assistant import (
    get_emmployee_courses,
)


employee_router = APIRouter(prefix="/employees", tags=["employee"])


def _ensure_employee_exists(employee_id: str) -> None:
    if not mock_data.employee_exists(employee_id):
        raise HTTPException(
            status_code=404, detail=f"Employee '{employee_id}' not found"
        )


@employee_router.get("/{employee_id}/dashboard")
def get_employee_dashboard(
    employee_id: str,
):
    """Single aggregated payload for rendering the whole Employee View.

    In mock mode (``use_mock``/``X-Use-Mock-Data``) the payload is read from
    ``data/employees.json``; otherwise it is assembled from live integrations.
    """

    data = mock_json.get_employee_dashboard(employee_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"Employee '{employee_id}' not found"
        )
    return data

    response = {}
    response.update(
        {"courses": get_emmployee_courses(employee_id), "employee_id": employee_id}
    )
    response = EmployeeDashboard(**response)
    return response


@employee_router.get("/check/")
def check_endpoint():
    return {"message": "Check endpoint"}


@employee_router.get(
    "/{employee_id}/current-skills", response_model=SkillDetailResponse
)
def get_current_skills(employee_id: str) -> SkillDetailResponse:
    """Shaped like Team 1's SkillDetailResponse. See module docstring re: auth scoping gap."""
    _ensure_employee_exists(employee_id)
    return mock_data.get_skill_detail(employee_id)


@employee_router.get("/{employee_id}/roadmap", response_model=list[Roadmap])
def get_roadmap_for_employee(employee_id: str) -> Roadmap:
    """Mirrors Team 2's confirmed real contract:
    GET /api/v1/employees/{employee_id}/roadmap
    """
    roadmap = get_emmployee_courses(employee_id)
    return roadmap


@employee_router.get("/{employee_id}/quizzes", response_model=EmployeeQuizzesResponse)
def get_employee_quizzes(
    employee_id: str,
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(
        default=None, description="Filter by course name (case-insensitive)"
    ),
    mock: bool = Depends(use_mock_data),
) -> EmployeeQuizzesResponse:
    """Mirrors assessment contract 2.1: GET /api/v1/employees/{employee_id}/quizzes."""
    if mock:
        _ensure_employee_exists(employee_id)
        return mock_data.get_employee_quizzes(
            employee_id, limit=limit, offset=offset, search=search
        )
    return get_assessment_service().get_employee_quizzes(
        employee_id, limit=limit, offset=offset, search=search
    )


@employee_router.get(
    "/{employee_id}/quiz-attempts", response_model=EmployeeQuizAttemptsResponse
)
def get_employee_quiz_attempts(
    employee_id: str,
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(
        default=None, description="Filter by course or skill name (case-insensitive)"
    ),
    mock: bool = Depends(use_mock_data),
) -> EmployeeQuizAttemptsResponse:
    """Mirrors assessment contract 2.3: GET /api/v1/employees/{employee_id}/quiz-attempts (cross-quiz)."""
    if mock:
        _ensure_employee_exists(employee_id)
        return mock_data.get_employee_quiz_attempts(
            employee_id, limit=limit, offset=offset, search=search
        )
    return get_assessment_service().get_employee_quiz_attempts(
        employee_id, limit=limit, offset=offset, search=search
    )
