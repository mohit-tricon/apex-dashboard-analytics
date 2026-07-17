"""Learning Assistant service integration.

Concrete BaseIntegration implementation for Team 2 (Learning Assistant).

All requests go through make_request() so they are:
- timed
- logged
- persisted to integration_logs
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from apex_dashboard_analytics.core.config import get_settings
from apex_dashboard_analytics.integrations.base import BaseIntegration


class LearningAssistantIntegration(BaseIntegration):
    """Client for the Learning Assistant service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float |None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        settings = get_settings()

        super().__init__(
            base_url or settings.learning_assistant_base_url,
            timeout=timeout or settings.integration_timeout_seconds,
            default_headers=default_headers,
        )

    @property
    def integration_name(self) -> str:
        return "learning_assistant"

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    def create_courses(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        POST /api/v1/courses
        """

        response = self.make_request(
            "POST",
            "/api/v1/courses",
            json=dict(payload),
        )

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Roadmap
    # ------------------------------------------------------------------

    def generate_roadmap(
        self,
        skill_id: str | UUID,
    ) -> dict[str, Any]:
        """
        POST /api/v1/skills/{skill_id}/roadmap
        """

        response = self.make_request(
            "POST",
            f"/api/v1/skills/{skill_id}/roadmap",
        )

        response.raise_for_status()
        return response.json()

    def get_employee_roadmaps(
        self,
        employee_id: str | UUID,
        *,
        skill_id: str | UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        GET /api/v1/employees/{employee_id}/roadmaps
        """

        params = {}

        if skill_id:
            params["skill_id"] = str(skill_id)

        response = self.make_request(
            "GET",
            f"/api/v1/employees/{employee_id}/roadmaps",
            params=params,
        )

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """
        Returns True if Learning Assistant is reachable.
        """

        try:
            response = self.make_request(
                "GET",
                "/health",
            )

            return response.status_code == 200

        except Exception:
            return False