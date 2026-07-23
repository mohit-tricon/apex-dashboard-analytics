"""Manager View endpoints.

Backs the Manager dashboard: team skill distribution, skill gaps,
training completion, and certification status.
"""

from __future__ import annotations

from fastapi import HTTPException, Query
from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_json
from apex_dashboard_analytics.services.dashboard_service import ManagerDashboardService

manager_router = APIRouter(prefix="/manager", tags=["manager"])


@manager_router.get("/{manager_id}/dashboard")
async def get_manager_dashboard(
    manager_id: str,
    use_actual_data: bool = Query(
        default=True,
        description="When true, assemble the dashboard from live integrations. "
        "Defaults to false, which returns mock data from data/managers.json.",
    ),
):
    """Single aggregated payload for rendering the whole Manager View.

    In mock mode the payload is read from ``data/managers.json``.
    """
    if not use_actual_data:
        data = mock_json.get_manager_dashboard(manager_id)
        if data is None:
            raise HTTPException(
                status_code=404, detail=f"Manager '{manager_id}' not found"
            )
        return data

    return await ManagerDashboardService(manager_id=manager_id).build()


# @manager_router.get(
#     "/{manager_id}/team/skill-distribution",
#     response_model=list[TeamSkillDistributionEntry],
# )
# def get_team_skill_distribution(manager_id: str) -> list[TeamSkillDistributionEntry]:
#     return mock_data.get_manager_dashboard(manager_id).team_skill_distribution


# @manager_router.get("/{manager_id}/team/skill-gaps", response_model=list[SkillGap])
# def get_team_skill_gaps(manager_id: str) -> list[SkillGap]:
#     return mock_data.get_manager_dashboard(manager_id).skill_gaps


# @manager_router.get(
#     "/{manager_id}/team/training-completion",
#     response_model=list[TrainingCompletionEntry],
# )
# def get_team_training_completion(manager_id: str) -> list[TrainingCompletionEntry]:
#     return mock_data.get_manager_dashboard(manager_id).training_completion


# @manager_router.get(
#     "/{manager_id}/team/certification-status",
#     response_model=list[CertificationStatusEntry],
# )
# def get_team_certification_status(manager_id: str) -> list[CertificationStatusEntry]:
#     return mock_data.get_manager_dashboard(manager_id).certification_status
