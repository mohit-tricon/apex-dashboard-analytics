"""AI Tutor service integration.

Concrete BaseIntegration implementation for Team 3 (AI Tutor).

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


class AITutorIntegration(BaseIntegration):
    """Client for the AI Tutor service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        settings = get_settings()

        super().__init__(
            base_url or settings.ai_tutor_base_url,
            timeout=timeout or settings.integration_timeout_seconds,
            default_headers=default_headers,
        )

    @property
    def integration_name(self) -> str:
        return "ai_tutor"

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_user_summary(
        self,
        user_id: str | UUID,
    ) -> dict[str, Any]:
        """
        GET /tutor/analytics/user/{user_id}/summary
        """
        response = self.make_request(
            "GET",
            f"/tutor/analytics/user/{user_id}/summary",
        )

        response.raise_for_status()
        return response.json()

    def get_user_skills(
        self,
        user_id: str | UUID,
    ) -> dict[str, Any]:
        """
        GET /tutor/analytics/user/{user_id}/skills
        """
        response = self.make_request(
            "GET",
            f"/tutor/analytics/user/{user_id}/skills",
        )

        response.raise_for_status()
        return response.json()

    def get_overview(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """
        GET /tutor/analytics/overview
        """
        params = {}

        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.make_request(
            "GET",
            "/tutor/analytics/overview",
            params=params,
        )

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """
        Returns True if AI Tutor is reachable.
        """
        try:
            response = self.make_request(
                "GET",
                "/health",
            )
            return response.status_code == 200
        except Exception:
            return False
