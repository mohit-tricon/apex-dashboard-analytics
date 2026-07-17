"""Orchestrates assessment service integration."""

from __future__ import annotations

import httpx
from fastapi import HTTPException

from apex_dashboard_analytics.core.logging import get_logger
from apex_dashboard_analytics.integrations.assessment import AssessmentIntegration
from apex_dashboard_analytics.schemas.assessment import (
    EmployeeAssessmentAttemptsResponse,
    EmployeeAssessmentsResponse,
)
from apex_dashboard_analytics.schemas.quiz import (
    EmployeeQuizAttemptsResponse,
    EmployeeQuizzesResponse,
    QuizAttemptsResponse,
)
from apex_dashboard_analytics.services.assessment_mapper import (
    map_assessments_to_quizzes,
    map_attempts_to_employee_quiz_attempts,
    map_attempts_to_quiz_attempts,
)

logger = get_logger(__name__)


class AssessmentService:
    """Facade for employee quiz endpoints backed by the assessment service."""

    def __init__(self, integration: AssessmentIntegration | None = None) -> None:
        self._integration = integration or AssessmentIntegration()

    def get_employee_quizzes(
        self,
        employee_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> EmployeeQuizzesResponse:
        try:
            raw = self._integration.get_employee_assessments(
                employee_id, limit=limit, offset=offset, search=search
            )
            assessments_response = EmployeeAssessmentsResponse.model_validate(raw)
            return map_assessments_to_quizzes(
                assessments_response, employee_id, limit=limit, offset=offset, search=search
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found") from exc
            raise self._service_unavailable("get_employee_quizzes", exc) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise self._service_unavailable("get_employee_quizzes", exc) from exc

    def get_employee_quiz_attempts(
        self,
        employee_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> EmployeeQuizAttemptsResponse:
        try:
            raw = self._integration.get_employee_assessment_attempts(
                employee_id, limit=limit, offset=offset, search=search
            )
            attempts_response = EmployeeAssessmentAttemptsResponse.model_validate(raw)
            return map_attempts_to_employee_quiz_attempts(
                attempts_response, employee_id, limit=limit, offset=offset, search=search
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found") from exc
            raise self._service_unavailable("get_employee_quiz_attempts", exc) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise self._service_unavailable("get_employee_quiz_attempts", exc) from exc

    def get_quiz_attempts(
        self,
        quiz_id: str,
        employee_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> QuizAttemptsResponse:
        try:
            raw = self._integration.get_employee_assessment_attempts(
                employee_id, limit=100, offset=0
            )
            attempts_response = EmployeeAssessmentAttemptsResponse.model_validate(raw)
            result = map_attempts_to_quiz_attempts(
                attempts_response, quiz_id=quiz_id, employee_id=employee_id, limit=limit, offset=offset
            )
            if result is None:
                raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found")
            return result
        except HTTPException:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found") from exc
            raise self._service_unavailable("get_quiz_attempts", exc) from exc
        except Exception as exc:
            raise self._service_unavailable("get_quiz_attempts", exc) from exc

    def _service_unavailable(self, operation: str, exc: Exception) -> HTTPException:
        logger.warning(
            "assessment_integration_failed",
            operation=operation,
            error=repr(exc),
        )
        return HTTPException(status_code=502, detail="Assessment service unavailable")


_assessment_service: AssessmentService | None = None


def get_assessment_service() -> AssessmentService:
    """Return a module-level singleton assessment service."""
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service
