"""Transform assessment service responses into frontend quiz contract models."""

from __future__ import annotations

from datetime import datetime

from apex_dashboard_analytics.constants import FAIL, NOT_STARTED, PASS, PASSED, FAILED
from apex_dashboard_analytics.schemas.assessment import (
    AssessmentAttemptRecord,
    AssessmentRecord,
    EmployeeAssessmentAttemptsResponse,
    EmployeeAssessmentsResponse,
)
from apex_dashboard_analytics.schemas.quiz import (
    EmployeeQuizAttempt,
    EmployeeQuizAttemptsResponse,
    EmployeeQuizzesResponse,
    Pagination,
    QuizAttempt,
    QuizAttemptsResponse,
    QuizSummary,
    QuizStatus,
    AttemptStatus,
)

# Default until assessment service or course→skill ontology mapping is available.
_DEFAULT_SKILL_ID = ""


def normalize_quiz_status(assessment_status: str) -> QuizStatus:
    """Map assessment service status to frontend quiz summary status."""
    if assessment_status == PASS:
        return PASSED
    if assessment_status == FAIL:
        return FAILED
    return NOT_STARTED


def normalize_attempt_status(assessment_status: str) -> AttemptStatus | None:
    """Map assessment status to attempt status; skip pending/in-progress rows."""
    if assessment_status == PASS:
        return PASSED
    if assessment_status == FAIL:
        return FAILED
    return None


def _paginate(items: list, limit: int, offset: int) -> tuple[list, Pagination]:
    total = len(items)
    page = items[offset : offset + limit]
    return page, Pagination(limit=limit, offset=offset, total=total, has_more=(offset + limit) < total)


def _latest_assessments_per_course(assessments: list[AssessmentRecord]) -> list[AssessmentRecord]:
    """Keep the last assessment row per course_id (most recent in upstream order)."""
    by_course: dict[str, AssessmentRecord] = {}
    for assessment in assessments:
        by_course[assessment.course_id] = assessment
    return list(by_course.values())


def _assessment_to_quiz_summary(assessment: AssessmentRecord) -> QuizSummary:
    return QuizSummary(
        quiz_id=assessment.course_id,
        skill_id=_DEFAULT_SKILL_ID,
        course=assessment.course,
        last_score=assessment.last_score,
        pass_threshold=assessment.pass_threshold,
        status=normalize_quiz_status(assessment.status),
    )


def map_assessments_to_quizzes(
    assessments_response: EmployeeAssessmentsResponse,
    employee_id: str,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
) -> EmployeeQuizzesResponse:
    """Group assessments by course and map to frontend quiz summaries."""
    grouped = _latest_assessments_per_course(assessments_response.assessments)
    quizzes = [_assessment_to_quiz_summary(a) for a in grouped]

    if search:
        needle = search.lower()
        quizzes = [q for q in quizzes if needle in q.course.lower() or needle in q.quiz_id.lower()]

    page, pagination = _paginate(quizzes, limit, offset)
    return EmployeeQuizzesResponse(
        employee_id=employee_id,
        quizzes=page,
        pagination=pagination,
    )


def _attempt_to_quiz_attempt(attempt: AssessmentAttemptRecord) -> QuizAttempt | None:
    status = normalize_attempt_status(attempt.status)
    if status is None:
        return None
    return QuizAttempt(
        course=attempt.course,
        score=attempt.score,
        status=status,
        attempted_on=attempt.attempted_on,
        feedback=attempt.feedback or "",
    )


def _attempt_to_employee_quiz_attempt(attempt: AssessmentAttemptRecord) -> EmployeeQuizAttempt | None:
    status = normalize_attempt_status(attempt.status)
    if status is None:
        return None
    return EmployeeQuizAttempt(
        quiz_id=attempt.course_id,
        skill_id=_DEFAULT_SKILL_ID,
        course=attempt.course,
        score=attempt.score,
        status=status,
        attempted_on=attempt.attempted_on,
        feedback=attempt.feedback or "",
    )


def _sort_attempts_by_date(items: list, key_fn) -> list:
    return sorted(
        items,
        key=lambda item: key_fn(item) or datetime.min.replace(tzinfo=None),
        reverse=True,
    )


def map_attempts_to_employee_quiz_attempts(
    attempts_response: EmployeeAssessmentAttemptsResponse,
    employee_id: str,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
) -> EmployeeQuizAttemptsResponse:
    """Map cross-quiz attempt history to the frontend contract."""
    rows: list[EmployeeQuizAttempt] = []
    for attempt in attempts_response.attempts:
        mapped = _attempt_to_employee_quiz_attempt(attempt)
        if mapped is not None:
            rows.append(mapped)

    if search:
        needle = search.lower()
        rows = [
            r for r in rows
            if needle in r.course.lower() or needle in r.quiz_id.lower() or needle in r.skill_id.lower()
        ]

    rows = _sort_attempts_by_date(rows, lambda r: r.attempted_on)
    page, pagination = _paginate(rows, limit, offset)
    return EmployeeQuizAttemptsResponse(
        employee_id=employee_id,
        attempts=page,
        pagination=pagination,
    )


def map_attempts_to_quiz_attempts(
    attempts_response: EmployeeAssessmentAttemptsResponse,
    *,
    quiz_id: str,
    employee_id: str,
    limit: int,
    offset: int,
) -> QuizAttemptsResponse | None:
    """Filter employee attempts by course_id (quiz_id) and map to single-quiz response."""
    filtered: list[QuizAttempt] = []
    for attempt in attempts_response.attempts:
        if attempt.course_id != quiz_id:
            continue
        mapped = _attempt_to_quiz_attempt(attempt)
        if mapped is not None:
            filtered.append(mapped)

    if not filtered:
        return None

    filtered = _sort_attempts_by_date(filtered, lambda a: a.attempted_on)
    page, pagination = _paginate(filtered, limit, offset)
    return QuizAttemptsResponse(
        employee_id=employee_id,
        quiz_id=quiz_id,
        attempts=page,
        pagination=pagination,
    )
