"""Skill Profiler service integration.

A concrete :class:`BaseIntegration` for the Skill Profiler team's service.
All requests are made through ``make_request`` so they are timed, logged via
the application logger, and persisted to ``integration_logs`` automatically.
"""

from __future__ import annotations

from typing import Any, Mapping

from apex_dashboard_analytics.core.config import get_settings
from apex_dashboard_analytics.integrations.base import BaseIntegration


class SkillProfilerIntegration(BaseIntegration):
    """Client for the Skill Profiler service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            base_url or settings.skill_profiler_base_url,
            timeout=timeout or settings.integration_timeout_seconds,
            default_headers=default_headers,
        )

    @property
    def integration_name(self) -> str:
        return "skill_profiler"

    # ------------------------------------------------------------------ #
    # API methods
    # ------------------------------------------------------------------ #
    def get_skill_profile(self, employee_id: str) -> dict[str, Any]:
        """Fetch an employee's skill profile."""
        response = self.make_request("GET", f"/employees/{employee_id}/skill-profile")
        response.raise_for_status()
        return response.json()

    def list_skills(self, *, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """List available skills (optionally filtered via query params)."""
        response = self.make_request("GET", "/skills", params=params)
        response.raise_for_status()
        return response.json()

    def upsert_skill_profile(
        self, employee_id: str, profile: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Create or update an employee's skill profile."""
        response = self.make_request(
            "PUT",
            f"/employees/{employee_id}/skill-profile",
            json=dict(profile),
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Return ``True`` if the service is reachable and healthy."""
        try:
            response = self.make_request("GET", "/health")
            return response.status_code == 200
        except Exception:
            # make_request already logged + persisted the failure.
            return False
