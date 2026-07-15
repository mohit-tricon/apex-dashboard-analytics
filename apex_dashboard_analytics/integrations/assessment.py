"""Assessment service integration.

Concrete :class:`BaseIntegration` for the Assessment & Quiz Agent service.
All requests go through ``make_request`` for timing, logging, and
``integration_logs`` persistence.
"""

from __future__ import annotations

from typing import Any, Mapping

from apex_dashboard_analytics.core.config import get_settings
from apex_dashboard_analytics.integrations.base import BaseIntegration


class AssessmentIntegration(BaseIntegration):
    """Client for the Assessment service."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | None = None,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            base_url or settings.assessment_base_url,
            timeout=timeout or settings.integration_timeout_seconds,
            default_headers=default_headers,
        )

    @property
    def integration_name(self) -> str:
        return "assessment"

    def get_employee_assessments(
        self,
        user_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> dict[str, Any]:
        """Fetch paginated assessment summaries for an employee."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        response = self.make_request(
            "GET",
            f"/assessment/results/employees/{user_id}/assessments",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_employee_assessment_attempts(
        self,
        user_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> dict[str, Any]:
        """Fetch paginated cross-assessment attempt history for an employee."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        response = self.make_request(
            "GET",
            f"/assessment/results/employees/{user_id}/assessment-attempts",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_course_assessment_attempts(
        self,
        course_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch paginated attempts for all users on a course."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = self.make_request(
            "GET",
            f"/assessment/results/courses/{course_id}/assessment-attempts",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Return ``True`` if the service is reachable and healthy."""
        try:
            response = self.make_request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False
