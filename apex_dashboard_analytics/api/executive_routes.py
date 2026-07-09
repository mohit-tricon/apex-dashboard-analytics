"""Executive View endpoints.

Backs the Executive dashboard: org-wide AI readiness score,
department-wise skills, and training ROI.
"""

from __future__ import annotations

from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_store
from apex_dashboard_analytics.schemas import DepartmentSkillEntry, ExecutiveDashboard
from apex_dashboard_analytics.schemas.dashboard import TrainingROI

executive_router = APIRouter(prefix="/executive", tags=["executive"])


@executive_router.get("/dashboard", response_model=ExecutiveDashboard)
def get_executive_dashboard() -> ExecutiveDashboard:
    """Single aggregated payload for rendering the whole Executive View."""
    return mock_store.get_executive_dashboard()


@executive_router.get("/ai-readiness-score")
def get_ai_readiness_score() -> dict:
    dashboard = mock_store.get_executive_dashboard()
    return {"org_ai_readiness_score": dashboard.org_ai_readiness_score}


@executive_router.get("/department-skills", response_model=list[DepartmentSkillEntry])
def get_department_skills() -> list[DepartmentSkillEntry]:
    return mock_store.get_executive_dashboard().department_skills


@executive_router.get("/training-roi", response_model=TrainingROI)
def get_training_roi() -> TrainingROI:
    return mock_store.get_executive_dashboard().training_roi