"""Dashboard aggregation services (employee / manager / executive).

Each service fans out its independent integration calls concurrently via the
worker-thread pool (``gather_sections``), then parses + assembles the result
into the corresponding ``data/*.json`` shape. A slow/failing upstream never
breaks the dashboard: failed sections are isolated and defaulted.
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
            # "assessments": self._assessments,
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


class ManagerDashboardService:
    """Aggregates a manager's dashboard from upstream integrations.

    Two-phase build:
      1. Get the manager's profile and basic team list concurrently.
      2. For each team member, fan out per-employee detail calls (skill profile,
         assessments, learning roadmap) and assemble member summaries.
    """

    def __init__(self, manager_id: str) -> None:
        self.manager_id = manager_id
        self._skills = SkillProfilerIntegration()
        self._assessment = AssessmentIntegration()
        self._tutor = AITutorIntegration()
        self._learning = LearningAssistantIntegration()

    # ------------------------------------------------------------------ #
    # Phase 1 – basic info
    # ------------------------------------------------------------------ #
    def _manager_profile(self) -> Any:
        raw = self._skills.get_user_profile(self.manager_id)
        return parsers.parse_manager_profile(raw)

    def _manager_team_basic(self) -> Any:
        raw = self._skills.get_manager_team(self.manager_id)
        return parsers.parse_manager_team(raw)

    # ------------------------------------------------------------------ #
    # Phase 2 – per-employee detail calls
    # ------------------------------------------------------------------ #
    @staticmethod
    def _member_calls(
        skills: SkillProfilerIntegration,
        assessment: AssessmentIntegration,
        learning: LearningAssistantIntegration,
        employee_id: str,
    ) -> dict[str, Any]:
        calls: dict[str, Any] = {}
        calls[f"skill_{employee_id}"] = lambda eid=employee_id: (
            parsers.parse_skill_profile(skills.get_skill_profile(eid))
        )
        calls[f"assess_{employee_id}"] = lambda eid=employee_id: (
            parsers.parse_assessments(assessment.get_employee_assessments(eid))
        )
        calls[f"roadmap_{employee_id}"] = lambda eid=employee_id: parsers.parse_roadmap(
            learning.get_employee_roadmaps(eid)
        )
        return calls

    async def _fetch_member_details(
        self,
        members: list[dict[str, Any]],
        settings: Any,
    ) -> list[dict[str, Any]]:
        if not members:
            return []
        calls: dict[str, Any] = {}
        for m in members:
            uid = m.get("employeeId")
            if uid:
                calls.update(
                    self._member_calls(
                        self._skills, self._assessment, self._learning, uid
                    )
                )
        results = await gather_sections(
            calls,
            per_call_timeout=settings.integration_timeout_seconds,
            total_timeout=settings.dashboard_total_timeout_seconds,
        )
        member_summaries: list[dict[str, Any]] = []
        for m in members:
            uid = m.get("employeeId")
            if not uid:
                continue
            skill_result = _section(results, f"skill_{uid}")
            assess_result = _section(results, f"assess_{uid}")
            roadmap_result = _section(results, f"roadmap_{uid}")
            member_summaries.append(
                parsers.parse_member_summary(
                    employee_id=uid,
                    name=m.get("name"),
                    skill_profile=skill_result,
                    assessments=assess_result,
                    roadmap=roadmap_result,
                )
            )
        return member_summaries

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
        settings = get_settings()

        # Phase 1: manager profile + team list
        phase1 = {
            "manager_profile": self._manager_profile,
            "manager_team_basic": self._manager_team_basic,
        }
        p1_results = await gather_sections(
            phase1,
            per_call_timeout=settings.integration_timeout_seconds,
            total_timeout=settings.dashboard_total_timeout_seconds,
        )

        manager = _section(p1_results, "manager_profile")
        members = _section(p1_results, "manager_team_basic") or []

        # Phase 2: per-employee details
        try:
            member_details = await self._fetch_member_details(members, settings)
        finally:
            await anyio.to_thread.run_sync(self.close)

        return parsers.assemble_manager_dashboard(
            self.manager_id,
            manager=manager,
            members=member_details,
        )


class ExecutiveDashboardService:
    """Aggregates the org-wide executive dashboard from upstream integrations.

    Fans out the AI Tutor org overview and the SkillProfiler skill catalog.
    NOTE: no upstream endpoint exposes per-department rollups yet, so
    department-level sections are empty/None until such a source is wired
    (pass parsed rollups via ``assemble_executive_dashboard(departments=...)``).
    """

    def __init__(self, *, name: str | None = None) -> None:
        self.name = name
        self._tutor = AITutorIntegration()
        self._skills = SkillProfilerIntegration()

    def _org_overview(self) -> Any:
        raw = self._tutor.get_overview()
        return parsers.parse_org_overview(raw)

    def _skill_catalog(self) -> Any:
        return self._skills.list_skills()

    def close(self) -> None:
        for integration in (self._tutor, self._skills):
            try:
                integration.close()
            except Exception:  # noqa: BLE001 - never fail on cleanup
                pass

    async def build(self) -> dict[str, Any]:
        settings = get_settings()
        calls = {
            "org_overview": self._org_overview,
            "skill_catalog": self._skill_catalog,
        }
        try:
            results = await gather_sections(
                calls,
                per_call_timeout=settings.integration_timeout_seconds,
                total_timeout=settings.dashboard_total_timeout_seconds,
            )
        finally:
            await anyio.to_thread.run_sync(self.close)

        return parsers.assemble_executive_dashboard(
            name=self.name,
            overview=_section(results, "org_overview"),
            departments=[],  # no per-department rollup endpoint upstream yet
        )


def _section(results: dict[str, Any], label: str) -> Any:
    """Return a section's parsed data if it succeeded, else None."""
    result = results.get(label)
    return result.data if result and result.ok else None
