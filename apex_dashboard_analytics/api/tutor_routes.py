"""Mirrors Team 3's read-only analytics contract (§4 of their doc).

NOTE: registered WITHOUT the /api/v1 prefix — Team 3's paths are
literally /tutor/analytics/..., unlike every other team's /api/v1/...
convention. See main.py for how this router is mounted.

The path param is named `user_id` to match Team 3's literal contract
(they don't use `employee_id`) — see schemas/tutoring.py docstring for
the unconfirmed employee_id <-> user_id mapping gap.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_data
from apex_dashboard_analytics.schemas import EmployeeAnalyticsSummary, EmployeeSkillAnalytics, TutorAnalyticsOverview

tutor_router = APIRouter(
    prefix="/tutor/analytics",
    tags=["tutor-analytics"],
    default_response_class=JSONResponse,
)


@tutor_router.get("/user/{user_id}/summary", response_model=EmployeeAnalyticsSummary)
def get_user_summary(user_id: str) -> EmployeeAnalyticsSummary:
    summary = mock_data.get_employee_analytics_summary(user_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"No tutor analytics found for user '{user_id}'")
    return summary


@tutor_router.get("/user/{user_id}/skills", response_model=EmployeeSkillAnalytics)
def get_user_skills(user_id: str) -> EmployeeSkillAnalytics:
    breakdown = mock_data.get_employee_skill_analytics(user_id)
    if breakdown is None:
        raise HTTPException(status_code=404, detail=f"No tutor skill analytics found for user '{user_id}'")
    return breakdown


@tutor_router.get("/overview", response_model=TutorAnalyticsOverview)
def get_overview(
    from_: date | None = Query(default=None, alias="from", description="Start date (default: 30 days ago)"),
    to: date | None = Query(default=None, description="End date (default: today)"),
) -> TutorAnalyticsOverview:
    today = date.today()
    start = from_ or (today - timedelta(days=30))
    end = to or today
    return mock_data.get_tutor_analytics_overview(str(start), str(end))