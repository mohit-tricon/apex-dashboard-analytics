"""Pydantic request/response models for the dashboard API.

These mirror the real inter-team API contracts shared by Teams 1, 2,
3, and 4 , plus Team 5's own composite
dashboard views.
"""

from __future__ import annotations

from apex_dashboard_analytics.schemas.skills import SkillDetailResponse, SkillGapItem
from apex_dashboard_analytics.schemas.learning import Roadmap, RoadmapCourse, RoadmapPlan, RoadmapWeek
from apex_dashboard_analytics.schemas.tutoring import (
    EmployeeAnalyticsSummary,
    EmployeeSkillAnalytics,
    EmployeeSkillInteraction,
    TutorAnalyticsOverview,
    TutorAnalyticsPeriod,
    TopSkillBySessionCount,
    TopUngroundedSkill,
)
from apex_dashboard_analytics.schemas.quiz import (
    Pagination,
    QuizSummary,
    EmployeeQuizzesResponse,
    QuizAttempt,
    QuizAttemptsResponse,
    EmployeeQuizAttempt,
    EmployeeQuizAttemptsResponse,
)
from apex_dashboard_analytics.schemas.dashboard import (
    EmployeeDashboard,
    EmployeeDashboardSummary,
    ManagerDashboard,
    ExecutiveDashboard,
    TeamSkillDistributionEntry,
    SkillGap,
    TrainingCompletionEntry,
    CertificationStatusEntry,
    DepartmentSkillEntry,
    TrainingROI,
)

__all__ = [
    "SkillDetailResponse",
    "SkillGapItem",
    "Roadmap",
    "RoadmapCourse",
    "RoadmapPlan",
    "RoadmapWeek",
    "EmployeeAnalyticsSummary",
    "EmployeeSkillAnalytics",
    "EmployeeSkillInteraction",
    "TutorAnalyticsOverview",
    "TutorAnalyticsPeriod",
    "TopSkillBySessionCount",
    "TopUngroundedSkill",
    "Pagination",
    "QuizSummary",
    "EmployeeQuizzesResponse",
    "QuizAttempt",
    "QuizAttemptsResponse",
    "EmployeeQuizAttempt",
    "EmployeeQuizAttemptsResponse",
    "EmployeeDashboard",
    "EmployeeDashboardSummary",
    "ManagerDashboard",
    "ExecutiveDashboard",
    "TeamSkillDistributionEntry",
    "SkillGap",
    "TrainingCompletionEntry",
    "CertificationStatusEntry",
    "DepartmentSkillEntry",
    "TrainingROI",
]