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
        default_headers = {
            **(default_headers or {}),
            "X-API-Key": settings.skill_profiler_api_key,
            # "X-Acting-Employee-Id": 123
        }
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

    def get_user_profile(self, employee_id: str) -> dict[str, Any]:
        """Fetch an employee's skill profile."""
        """Expected Response
            {
            "userId": "string",
            "username": "string",
            "email": "string",
            "role": "ADMIN",
            "reportsTo": "string",
            "reportsToName": "string"
            }
        """

        response = self.make_request(
            "GET",
            "/api/v1/me",
            headers={**self.default_headers, "X-Acting-Employee-Id": employee_id},
        )

        return response.json()

    def get_skill_profile(self, employee_id: str) -> dict[str, Any]:
        """Fetch an employee's skill profile."""
        """Expected Response [
            {
                "skillId": "string",
                "userId": "string",
                "username": "string",
                "email": "string",
                "currentRole": "string",
                "targetRole": "string",
                "skills": {
                "additionalProp1": 0,
                "additionalProp2": 0,
                "additionalProp3": 0
                },
                "skillGaps": [
                {
                    "skill": "string",
                    "requiredLevel": 0
                }
                ],
                "roleAlignment": "string",
                "resumePath": "string",
                "status": "string",
                "createdAt": "2026-07-21T07:27:11.879Z",
                "llmProvider": "string",
                "llmModel": "string"
            }
            ]
        """

        response = self.make_request(
            "GET",
            "/api/v1/skill-analysis",
            headers={**self.default_headers, "X-Acting-Employee-Id": employee_id},
        )

        return response.json()

    def get_manager_team(self, manager_id: str) -> dict[str, Any]:
        """Fetch an employee's skill profile."""
        """Expected Response 
        [
            {
                "userId": "string",
                "username": "string",
                "email": "string",
                "role": "ADMIN",
                "reportsTo": "string",
                "reportsToName": "string",
                "assessmentCount": 0,
                "createdAt": "2026-07-21T13:04:16.745Z"
            }
        ]
        """

        response = self.make_request(
            "GET",
            "/api/v1/users",
            headers={**self.default_headers, "X-Acting-Employee-Id": manager_id},
        )

        return response.json()

    # def list_skills(self, *, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    #     """List available skills (optionally filtered via query params)."""
    #     response = self.make_request("GET", "/skills", params=params)

    #     return response.json()

    # Not using this method, hence deprecating
    # def upsert_skill_profile(
    #     self, employee_id: str, profile: Mapping[str, Any]
    # ) -> dict[str, Any]:
    #     """Create or update an employee's skill profile."""
    #     response = self.make_request(
    #         "PUT",
    #         f"/employees/{employee_id}/skill-profile",
    #         json=dict(profile),
    #     )

    #     return response.json()

    # def health_check(self) -> bool:
    #     """Return ``True`` if the service is reachable and healthy."""
    #     try:
    #         response = self.make_request("GET", "/health")
    #         return response.status_code == 200
    #     except Exception:
    #         # make_request already logged + persisted the failure.
    #         return False
