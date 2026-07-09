"""Employee View endpoints.

Two kinds of routes here:
  1. Team 5's own aggregated `/dashboard` endpoint (our design).
  2. Endpoints that mirror the other teams' real contracts.

Confirmed against real contracts as of 2026-07-09:
  - Team 4 (quizzes, quiz-attempts): matched exactly against their doc.
  - Team 2 (roadmap): matched exactly against their live Swagger docs
    (GET /api/v1/employees/{employee_id}/roadmap).

NOT yet confirmed:
  - Team 1 (current-skills): their real `GET /api/v1/skill-analysis` is
    scoped to the caller's own bearer token, not an `employee_id` path
    param, so `/employees/{employee_id}/current-skills` below is shaped
    like their response (`SkillDetailResponse`) but is not a literal
    proxy — the real integration needs either a manager-scoped endpoint
    from Team 1 or direct DB access. Flagged for follow-up.
  - Team 3 (AI Tutor): no contract shared yet. Not wired into this
    router at all until we get one.
"""

from __future__ import annotations

from fastapi import HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_store
from apex_dashboard_analytics.schemas import (
    EmployeeDashboard,
    EmployeeQuizAttemptsResponse,
    EmployeeQuizzesResponse,
    SkillDetailResponse,
)
from apex_dashboard_analytics.schemas.learning import Roadmap

employee_router = APIRouter(prefix="/employees", tags=["employee"])


def _ensure_employee_exists(employee_id: str) -> None:
    if not mock_store.employee_exists(employee_id):
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found")


@employee_router.get("/check/")
def check_endpoint():
    return {"message": "Check endpoint"}


@employee_router.get("/{employee_id}/dashboard", response_model=EmployeeDashboard)
def get_employee_dashboard(employee_id: str) -> EmployeeDashboard:
    """Single aggregated payload for rendering the whole Employee View."""
    _ensure_employee_exists(employee_id)
    return mock_store.get_employee_dashboard(employee_id)


@employee_router.get("/{employee_id}/current-skills", response_model=SkillDetailResponse)
def get_current_skills(employee_id: str) -> SkillDetailResponse:
    """Shaped like Team 1's SkillDetailResponse. See module docstring re: auth scoping gap."""
    _ensure_employee_exists(employee_id)
    return mock_store.get_skill_detail(employee_id)


@employee_router.get("/{employee_id}/roadmap", response_model=Roadmap)
def get_roadmap_for_employee(employee_id: str) -> Roadmap:
    """Mirrors Team 2's confirmed real contract:
    GET /api/v1/employees/{employee_id}/roadmap
    """
    _ensure_employee_exists(employee_id)
    roadmap = mock_store.get_roadmap_by_employee_id(employee_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail=f"No roadmap found for employee '{employee_id}'")
    return roadmap


@employee_router.get("/{employee_id}/quizzes", response_model=EmployeeQuizzesResponse)
def get_employee_quizzes(
    employee_id: str,
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, description="Filter by course name (case-insensitive)"),
) -> EmployeeQuizzesResponse:
    """Mirrors Team 4 contract 2.1: GET /api/v1/employees/{employee_id}/quizzes."""
    _ensure_employee_exists(employee_id)
    return mock_store.get_employee_quizzes(employee_id, limit=limit, offset=offset, search=search)


@employee_router.get("/{employee_id}/quiz-attempts", response_model=EmployeeQuizAttemptsResponse)
def get_employee_quiz_attempts(
    employee_id: str,
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, description="Filter by course or skill name (case-insensitive)"),
) -> EmployeeQuizAttemptsResponse:
    """Mirrors Team 4 contract 2.3: GET /api/v1/employees/{employee_id}/quiz-attempts (cross-quiz)."""
    _ensure_employee_exists(employee_id)
    return mock_store.get_employee_quiz_attempts(employee_id, limit=limit, offset=offset, search=search)