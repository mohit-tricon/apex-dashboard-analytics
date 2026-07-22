"""Executive View endpoints.

Backs the Executive dashboard: org-wide AI readiness score,
department-wise skills, and training ROI.
"""

from __future__ import annotations

from fastapi import HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_json
from apex_dashboard_analytics.services.dashboard_service import (
    ExecutiveDashboardService,
)

executive_router = APIRouter(prefix="/executive", tags=["executive"])


@executive_router.get("/dashboard")
async def get_executive_dashboard(
    use_actual_data: bool = Query(
        default=False,
        description="When true, assemble the dashboard from live integrations. "
        "Defaults to false, which returns mock data from data/executive.json.",
    ),
):
    """Single aggregated payload for rendering the whole Executive View.

    In mock mode the payload is read from ``data/executive.json``.
    """
    if not use_actual_data:
        data = mock_json.get_executive_dashboard()
        if data is None:
            raise HTTPException(
                status_code=404, detail="Executive dashboard data not found"
            )
        return data
    return await ExecutiveDashboardService().build()


# @executive_router.get("/ai-readiness-score")
# def get_ai_readiness_score() -> dict:
#     dashboard = mock_data.get_executive_dashboard()
#     return {"org_ai_readiness_score": dashboard.org_ai_readiness_score}


# @executive_router.get("/department-skills", response_model=list[DepartmentSkillEntry])
# def get_department_skills() -> list[DepartmentSkillEntry]:
#     return mock_data.get_executive_dashboard().department_skills


# @executive_router.get("/training-roi", response_model=TrainingROI)
# def get_training_roi() -> TrainingROI:
#     return mock_data.get_executive_dashboard().training_roi
