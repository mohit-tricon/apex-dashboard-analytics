"""Composite view models for the RBAC-gated dashboard.

Employee/Manager/Executive views, per the project brief:

    Employee View          Manager View             Executive View
    ------------------     ---------------------    -------------------
    Current Skill Score    Team Skill Distribution   AI Readiness Score
    Learning Progress      Skill Gaps                Dept-wise Skills
    Recommended Courses    Training Completion       Training ROI
    Quiz Scores            Certification Status

EmployeeDashboard now wraps the real upstream contract shapes
(SkillDetailResponse from Team 1, Roadmap from Team 2,
EmployeeQuizzesResponse/EmployeeQuizAttemptsResponse from Team 4)
instead of inventing a shape, plus a small derived `summary` block for
convenience. Manager/Executive views have no upstream contract yet —
they're Team 5's own aggregation design.
"""

from __future__ import annotations

from pydantic import BaseModel

from apex_dashboard_analytics.schemas.learning import Roadmap
from apex_dashboard_analytics.schemas.quiz import EmployeeQuizAttemptsResponse, EmployeeQuizzesResponse
from apex_dashboard_analytics.schemas.skills import SkillDetailResponse


# ---------------------------------------------------------------- Employee


class EmployeeDashboardSummary(BaseModel):
    """Small derived block so the frontend doesn't have to compute these."""

    open_skill_gaps: int
    roadmap_total_weeks: int | None = None
    total_quizzes: int
    quiz_pass_rate_percentage: float


class EmployeeDashboard(BaseModel):
    """Aggregated payload for the Employee View."""

    employee_id: str
    skill_profile: SkillDetailResponse
    roadmap: Roadmap | None = None
    quizzes: EmployeeQuizzesResponse
    recent_quiz_attempts: EmployeeQuizAttemptsResponse
    summary: EmployeeDashboardSummary


# ----------------------------------------------------------------- Manager


class TeamSkillDistributionEntry(BaseModel):
    skill_name: str
    employee_count: int
    average_score: float


class SkillGap(BaseModel):
    skill_name: str
    required_level: float
    current_average_level: float
    gap: float
    affected_employee_count: int


class TrainingCompletionEntry(BaseModel):
    employee_id: str
    employee_name: str
    quizzes_passed: int
    quizzes_total: int
    completion_percentage: float


class CertificationStatusEntry(BaseModel):
    employee_id: str
    employee_name: str
    role_alignment: str
    status: str  # "completed" | "in_progress" | "not_started" | "expired"


class ManagerDashboard(BaseModel):
    """Aggregated payload for the Manager View."""

    manager_id: str
    team_size: int
    team_skill_distribution: list[TeamSkillDistributionEntry]
    skill_gaps: list[SkillGap]
    training_completion: list[TrainingCompletionEntry]
    certification_status: list[CertificationStatusEntry]


# --------------------------------------------------------------- Executive


class DepartmentSkillEntry(BaseModel):
    department: str
    average_ai_readiness_score: float
    top_skill_gaps: list[str]
    headcount: int


class TrainingROI(BaseModel):
    total_training_hours: float
    total_training_cost_usd: float
    estimated_productivity_gain_usd: float
    roi_percentage: float


class ExecutiveDashboard(BaseModel):
    """Aggregated payload for the Executive View."""

    org_ai_readiness_score: float
    department_skills: list[DepartmentSkillEntry]
    training_roi: TrainingROI