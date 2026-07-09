"""Manager View endpoints.

Backs the Manager dashboard: team skill distribution, skill gaps,
training completion, and certification status.
"""

from __future__ import annotations

from fastapi.routing import APIRouter

from apex_dashboard_analytics.data import mock_store
from apex_dashboard_analytics.schemas import (
    CertificationStatusEntry,
    ManagerDashboard,
    SkillGap,
    TeamSkillDistributionEntry,
    TrainingCompletionEntry,
)

manager_router = APIRouter(prefix="/manager", tags=["manager"])


@manager_router.get("/{manager_id}/dashboard", response_model=ManagerDashboard)
def get_manager_dashboard(manager_id: str) -> ManagerDashboard:
    """Single aggregated payload for rendering the whole Manager View."""
    return mock_store.get_manager_dashboard(manager_id)


@manager_router.get("/{manager_id}/team/skill-distribution", response_model=list[TeamSkillDistributionEntry])
def get_team_skill_distribution(manager_id: str) -> list[TeamSkillDistributionEntry]:
    return mock_store.get_manager_dashboard(manager_id).team_skill_distribution


@manager_router.get("/{manager_id}/team/skill-gaps", response_model=list[SkillGap])
def get_team_skill_gaps(manager_id: str) -> list[SkillGap]:
    return mock_store.get_manager_dashboard(manager_id).skill_gaps


@manager_router.get("/{manager_id}/team/training-completion", response_model=list[TrainingCompletionEntry])
def get_team_training_completion(manager_id: str) -> list[TrainingCompletionEntry]:
    return mock_store.get_manager_dashboard(manager_id).training_completion


@manager_router.get("/{manager_id}/team/certification-status", response_model=list[CertificationStatusEntry])
def get_team_certification_status(manager_id: str) -> list[CertificationStatusEntry]:
    return mock_store.get_manager_dashboard(manager_id).certification_status