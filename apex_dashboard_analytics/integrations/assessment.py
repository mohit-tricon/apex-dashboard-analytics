"""Assessment service integration.

Concrete :class:`BaseIntegration` for the Assessment & Quiz Agent service.
All requests go through ``make_request`` for timing, logging, and
``integration_logs`` persistence.
"""

from __future__ import annotations

from typing import Any, Mapping

from apex_dashboard_analytics.core.config import get_settings
from apex_dashboard_analytics.integrations.base import BaseIntegration


def _authorization_header(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    value = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    return {"Authorization": value}


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
        headers = {
            **_authorization_header(settings.assessment_api_token),
            **(default_headers or {}),
        }
        super().__init__(
            base_url or settings.assessment_base_url,
            timeout=timeout or settings.integration_timeout_seconds,
            default_headers=headers,
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
        """Expected Response
            {
            "user_id": "string",
            "assessments": [
                {
                "assessment_id": "string",
                "course_id": "string",
                "course": "string",
                "last_score": 0,
                "pass_threshold": 0,
                "status": "string"
                }
            ],
            "pagination": {
                "additionalProp1": {}
            }
            }
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        response = self.make_request(
            "GET",
            f"/assessment/results/employees/{user_id}/assessments",
            params=params,
        )
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
        """Expected Response
            {
            "user_id": "string",
            "attempts": [
                {
                "assessment_id": "string",
                "course_id": "string",
                "course": "string",
                "score": 0,
                "status": "string",
                "attempted_on": "2026-07-21T07:31:23.088Z",
                "feedback": "string"
                }
            ],
            "pagination": {
                "additionalProp1": {}
            }
            }
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        response = self.make_request(
            "GET",
            f"/assessment/results/employees/{user_id}/assessment-attempts",
            params=params,
        )
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
        return response.json()

    def health_check(self) -> bool:
        """Return ``True`` if the service is reachable and healthy."""
        try:
            response = self.make_request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False
