from __future__ import annotations

import structlog
from fastapi import Depends, Header, HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_store
from apex_dashboard_analytics.schemas.tutoring import (
    UserAnalyticsSummary,
    UserSkillsBreakdown,
    TutorOverviewResponse,
    QuizResultWebhookPayload,
)

logger = structlog.get_logger(__name__)

tutor_router = APIRouter(prefix="/tutor", tags=["tutor"])


def verify_service_token(authorization: str | None = Header(default=None)) -> str:
    """Validate the service-role bearer token per the contract specifications.
    
    Accepts any bearer token for local development/simulation, but raises 401 if missing.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        logger.warning("unauthorized_service_role_access_attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid service-role token"
        )
    return authorization.split(" ")[1]


@tutor_router.post("/hooks/quiz-result", status_code=200)
def receive_quiz_result_webhook(
    payload: QuizResultWebhookPayload,
    token: str = Depends(verify_service_token)
) -> dict:
    """Team 4 -> Team 3: quiz completion notification.
    
    Validates if the user exists in Team 3's system, otherwise returns 404.
    """
    if not mock_store.employee_exists(payload.user_id):
        logger.warning("webhook_user_not_found", user_id=payload.user_id)
        raise HTTPException(
            status_code=404,
            detail="User or skill not found in Team 3's system"
        )
        
    return mock_store.add_quiz_result(payload)


@tutor_router.get("/analytics/user/{user_id}/summary", response_model=UserAnalyticsSummary)
def get_user_analytics_summary(
    user_id: str,
    token: str = Depends(verify_service_token)
) -> UserAnalyticsSummary:
    """Get user learning engagement summary for Team 5's dashboard."""
    if not mock_store.employee_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return mock_store.get_tutor_summary(user_id)


@tutor_router.get("/analytics/user/{user_id}/skills", response_model=UserSkillsBreakdown)
def get_user_skills_breakdown(
    user_id: str,
    token: str = Depends(verify_service_token)
) -> UserSkillsBreakdown:
    """Get per-skill interaction breakdown for Team 5's dashboard."""
    if not mock_store.employee_exists(user_id):
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return mock_store.get_tutor_skills(user_id)


@tutor_router.get("/analytics/overview", response_model=TutorOverviewResponse)
def get_tutor_overview_analytics(
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    token: str = Depends(verify_service_token)
) -> TutorOverviewResponse:
    """Get platform-wide tutor usage (executive/admin view) for Team 5's dashboard."""
    return mock_store.get_tutor_overview(from_date, to_date)
