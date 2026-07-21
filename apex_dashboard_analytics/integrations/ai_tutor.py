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
        """Expected Response
            {
            "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "total_sessions": 0,
            "total_messages": 0,
            "total_questions_asked": 0,
            "total_documents_uploaded": 0,
            "avg_messages_per_session": 0,
            "grounded_response_rate": 0,
            "feedback_given": 0,
            "thumbs_up_rate": 0,
            "first_interaction": "2026-07-21T07:32:36.311Z",
            "last_interaction": "2026-07-21T07:32:36.311Z",
            "active_skills_count": 0,
            "completed_skills_count": 0
            }
        """

        return response.json()

    def get_user_skills(
        self,
        user_id: str | UUID,
    ) -> dict[str, Any]:
        """
        GET /tutor/analytics/user/{user_id}/skills
        """

        """Expected Response
            {
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "skills": [
            {
            "skill_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "skill_name": "string",
            "skill_level": "string",
            "target_role": "string",
            "session_count": 0,
            "total_messages": 0,
            "total_questions": 0,
            "documents_uploaded": 0,
            "grounded_response_rate": 0,
            "thumbs_up_rate": 0,
            "last_interaction": "2026-07-21T07:33:54.554Z",
            "top_topics_asked": [],
            "guardrail_blocks": 0
            }
        ]
        }
        """

        response = self.make_request(
            "GET",
            f"/tutor/analytics/user/{user_id}/skills",
        )

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
