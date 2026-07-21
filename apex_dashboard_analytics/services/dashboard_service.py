"""Employee dashboard aggregation service.

Fans out the independent integration calls (SkillProfiler, Assessment,
AITutor, LearningAssistant) concurrently via the worker-thread pool, returning
partial data with a per-section status block so one slow/failing upstream never
breaks the whole dashboard.
"""

from __future__ import annotations

from typing import Any

import anyio

from apex_dashboard_analytics.core.config import get_settings
from apex_dashboard_analytics.core.logging import get_logger
from apex_dashboard_analytics.integrations.ai_tutor import AITutorIntegration
from apex_dashboard_analytics.integrations.assessment import AssessmentIntegration
from apex_dashboard_analytics.integrations.learning_assistant import (
    LearningAssistantIntegration,
)
from apex_dashboard_analytics.integrations.skill_profiler import (
    SkillProfilerIntegration,
)
from apex_dashboard_analytics.services import dashboard_parsers as parsers
from apex_dashboard_analytics.services.concurrency import gather_sections

logger = get_logger(__name__)


class EmployeeDashboardService:
    """Aggregates an employee's dashboard from multiple upstream integrations."""

    def __init__(self, employee_id: str) -> None:
        self.employee_id = employee_id
        # One instance per integration (reuses its HTTP client across its calls).
        self._skills = SkillProfilerIntegration()
        self._assessment = AssessmentIntegration()
        self._tutor = AITutorIntegration()
        self._learning = LearningAssistantIntegration()

    # ------------------------------------------------------------------ #
    # Sync unit calls (each runs in a worker thread; raises on failure)
    # ------------------------------------------------------------------ #
    def _skill_profile(self) -> Any:
        raw = self._skills.get_skill_profile(self.employee_id)
        return parsers.parse_skill_profile(raw)

    def _user_profile(self) -> Any:
        raw = self._skills.get_user_profile(self.employee_id)
        return parsers.parse_user_profile(raw)

    def _assessments(self) -> Any:
        raw = self._assessment.get_employee_assessments(self.employee_id)
        return parsers.parse_assessments(raw)

    def _assessment_attempts(self) -> Any:
        raw = self._assessment.get_employee_assessment_attempts(self.employee_id)
        return parsers.parse_assessment_attempts(raw)

    def _tutor_summary(self) -> Any:
        raw = self._tutor.get_user_summary(self.employee_id)
        return parsers.parse_tutor_summary(raw)

    def _tutor_skills(self) -> Any:
        raw = self._tutor.get_user_skills(self.employee_id)
        return parsers.parse_tutor_skills(raw)

    def _roadmap(self) -> Any:
        roadmaps = self._learning.get_employee_roadmaps(self.employee_id)
        return parsers.parse_roadmap(roadmaps)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        for integration in (
            self._skills,
            self._assessment,
            self._tutor,
            self._learning,
        ):
            try:
                integration.close()
            except Exception:  # noqa: BLE001 - never fail on cleanup
                pass

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    async def build(self) -> dict[str, Any]:
        """Concurrently gather all sections and assemble the dashboard payload."""
        settings = get_settings()

        calls = {
            "skill_profile": self._skill_profile,
            "user_profile": self._user_profile,
            "assessments": self._assessments,
            "assessment_attempts": self._assessment_attempts,
            "tutor_summary": self._tutor_summary,
            "tutor_skills": self._tutor_skills,
            "roadmap": self._roadmap,
        }

        try:
            results = await gather_sections(
                calls,
                per_call_timeout=settings.integration_timeout_seconds,
                total_timeout=settings.dashboard_total_timeout_seconds,
            )
        finally:
            await anyio.to_thread.run_sync(self.close)

        # Failed/timed-out sections are logged inside gather_sections; here we
        # tolerate them and let the assembler default missing pieces.
        def data(label: str) -> Any:
            result = results.get(label)
            return result.data if result and result.ok else None

        return parsers.assemble_employee_dashboard(
            self.employee_id,
            user_profile=data("user_profile"),
            skill_profile=data("skill_profile"),
            assessments=data("assessments"),
            roadmap=data("roadmap"),
        )
