"""Deterministic sample data for the dashboard endpoints.

Shapes here match the REAL contracts shared by Team 1 (skills), Team 2
(roadmap), Team 3 (tutor analytics), and Team 4 (quizzes) as of
2026-07-09 — see the schema modules for contract source notes and
known discrepancies.

Plain dicts/lists, no DB. Swap for real HTTP calls to
SKILL_PROFILER_BASE_URL / LEARNING_RECOMMENDATION_BASE_URL /
AI_TUTOR_BASE_URL / ASSESSMENT_BASE_URL (see .env.example) once those
services are live.
"""

from __future__ import annotations

from apex_dashboard_analytics.schemas.dashboard import (
    CertificationStatusEntry,
    DepartmentSkillEntry,
    EmployeeDashboard,
    EmployeeDashboardSummary,
    ExecutiveDashboard,
    ManagerDashboard,
    SkillGap,
    TeamSkillDistributionEntry,
    TrainingCompletionEntry,
    TrainingROI,
)
from apex_dashboard_analytics.schemas.learning import Roadmap, RoadmapCourse, RoadmapPlan, RoadmapWeek
from apex_dashboard_analytics.schemas.quiz import (
    EmployeeQuizAttempt,
    EmployeeQuizAttemptsResponse,
    EmployeeQuizzesResponse,
    Pagination,
    QuizAttempt,
    QuizAttemptsResponse,
    QuizSummary,
)
from apex_dashboard_analytics.schemas.skills import SkillDetailResponse, SkillGapItem
from apex_dashboard_analytics.schemas.tutoring import (
    EmployeeAnalyticsSummary,
    EmployeeSkillAnalytics,
    EmployeeSkillInteraction,
    TopSkillBySessionCount,
    TopUngroundedSkill,
    TutorAnalyticsOverview,
    TutorAnalyticsPeriod,
)

# --------------------------------------------------------------------------
# Fake "database" of employees. Keyed by employee_id (== Team 1's userId).
# skill_id is the id of that employee's latest skill-analysis record —
# it's what Team 2's roadmap endpoint keys off of.
# --------------------------------------------------------------------------

_EMPLOYEES: dict[str, dict] = {
    "usr_9823471": {
        "skill_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Asha Verma",
        "username": "asha.verma",
        "email": "asha.verma@example.com",
        "manager_id": "mgr_1001",
        "department": "Backend & Cloud Engineering",
        "current_role": "Python Dev",
        "target_role": "FastAPI Dev",
        "role_alignment": "PARTIAL",
        "skills": {"Python": 92, "FastAPI": 68, "AWS Cloud Architecture": 74},
        "skill_gaps": [{"skill": "FastAPI", "requiredLevel": 90}, {"skill": "Kubernetes", "requiredLevel": 80}],
    },
    "usr_9823472": {
        "skill_id": "5b2e9e10-8b2a-4b3e-9f1a-1c2d3e4f5a6b",
        "name": "Rohit Nair",
        "username": "rohit.nair",
        "email": "rohit.nair@example.com",
        "manager_id": "mgr_1001",
        "department": "Backend & Cloud Engineering",
        "current_role": "Junior Developer",
        "target_role": "Python Dev",
        "role_alignment": "NOT_ALIGNED",
        "skills": {"Python": 55, "SQL": 60},
        "skill_gaps": [{"skill": "Python", "requiredLevel": 85}, {"skill": "FastAPI", "requiredLevel": 70}],
    },
    "usr_9823473": {
        "skill_id": "9c1d2e3f-4a5b-4c6d-8e7f-0a1b2c3d4e5f",
        "name": "Priya Shah",
        "username": "priya.shah",
        "email": "priya.shah@example.com",
        "manager_id": "mgr_1001",
        "department": "Data & ML",
        "current_role": "Data Analyst",
        "target_role": "ML Engineer",
        "role_alignment": "PARTIAL",
        "skills": {"Python": 80, "Statistics": 75, "MLOps": 45},
        "skill_gaps": [{"skill": "MLOps", "requiredLevel": 85}, {"skill": "Model Evaluation", "requiredLevel": 80}],
    },
}

_SKILL_ID_TO_EMPLOYEE: dict[str, str] = {e["skill_id"]: uid for uid, e in _EMPLOYEES.items()}


# --------------------------------------------------------------------------
# Pagination / search helper
# --------------------------------------------------------------------------


def _paginate(items: list, limit: int, offset: int) -> tuple[list, Pagination]:
    total = len(items)
    page = items[offset : offset + limit]
    return page, Pagination(limit=limit, offset=offset, total=total, has_more=(offset + limit) < total)


# --------------------------------------------------------------------------
# Team 1 — skill profile  (mirrors SkillDetailResponse)
# --------------------------------------------------------------------------


def employee_exists(employee_id: str) -> bool:
    return employee_id in _EMPLOYEES


def get_skill_detail(employee_id: str) -> SkillDetailResponse:
    e = _EMPLOYEES[employee_id]
    return SkillDetailResponse(
        skillId=e["skill_id"],
        userId=employee_id,
        username=e["username"],
        email=e["email"],
        currentRole=e["current_role"],
        targetRole=e["target_role"],
        skills=e["skills"],
        skillGaps=[SkillGapItem(**g) for g in e["skill_gaps"]],
        roleAlignment=e["role_alignment"],
        resumePath=f"{e['skill_id']}/resume.pdf",
        status="COMPLETED",
        createdAt="2026-06-29T07:25:00Z",
        llmProvider="anthropic",
        llmModel="claude-sonnet-4-6",
    )


# --------------------------------------------------------------------------
# Team 2 — roadmap  (mirrors Roadmap / GET /employees/{employee_id}/roadmap)
# `get_roadmap_by_skill_id` is an internal helper only — Team 2 does not
# expose a skill_id-keyed route; kept here since the mock data is
# naturally modeled around skill_id internally.
# --------------------------------------------------------------------------


def get_roadmap_by_skill_id(skill_id: str) -> Roadmap | None:
    employee_id = _SKILL_ID_TO_EMPLOYEE.get(skill_id)
    if employee_id is None:
        return None
    e = _EMPLOYEES[employee_id]
    return Roadmap(
        roadmap_id=f"rm_{skill_id[:8]}",
        skill_id=skill_id,
        target_role=e["target_role"],
        status="active",
        plan=RoadmapPlan(
            summary=f"A 12-week roadmap to transition {e['name']} from {e['current_role']} to {e['target_role']}.",
            total_weeks=12,
            weeks=[
                RoadmapWeek(
                    week=1,
                    focus="Close the highest-priority skill gap first.",
                    skills=[g["skill"] for g in e["skill_gaps"][:1]],
                    courses=[
                        RoadmapCourse(
                            course_id="crs_fastapi_101",
                            course_name="FastAPI for Production APIs",
                            provider="Coursera",
                            url="https://www.coursera.org/learn/fastapi-for-production-apis",
                            duration_hours=10,
                            skills_taught=["FastAPI"],
                        )
                    ],
                    activities=["Set up a local FastAPI project.", "Complete module 1."],
                ),
                RoadmapWeek(
                    week=2,
                    focus="Deepen cloud fundamentals.",
                    skills=[g["skill"] for g in e["skill_gaps"][1:2]] or ["AWS Cloud Architecture"],
                    courses=[
                        RoadmapCourse(
                            course_id="crs_aws_saa",
                            course_name="AWS Solutions Architect Associate",
                            provider="Coursera",
                            url="https://www.coursera.org/specializations/aws-solutions-architect",
                            duration_hours=25,
                            skills_taught=["AWS"],
                        )
                    ],
                    activities=["Complete the first AWS module.", "Take the module quiz."],
                ),
            ],
        ),
        created_at="2026-07-07T09:06:52.279860Z",
    )


def get_roadmap_by_employee_id(employee_id: str) -> Roadmap | None:
    e = _EMPLOYEES.get(employee_id)
    if e is None:
        return None
    return get_roadmap_by_skill_id(e["skill_id"])


# --------------------------------------------------------------------------
# Team 4 — quizzes  (mirrors 2.1 / 2.2 / 2.3 exactly)
# --------------------------------------------------------------------------

_QUIZ_CATALOG: dict[str, list[dict]] = {
    "usr_9823471": [
        {"quiz_id": "Q101", "skill_id": "108", "course": "Learning FastAPI Fundamentals", "last_score": 82, "pass_threshold": 60, "status": "passed"},
        {"quiz_id": "Q102", "skill_id": "103", "course": "Learning Databases", "last_score": 40, "pass_threshold": 60, "status": "failed"},
    ],
    "usr_9823472": [
        {"quiz_id": "Q201", "skill_id": "101", "course": "Python Fundamentals", "last_score": 55, "pass_threshold": 60, "status": "failed"},
    ],
    "usr_9823473": [
        {"quiz_id": "Q301", "skill_id": "115", "course": "Statistics for ML", "last_score": 78, "pass_threshold": 60, "status": "passed"},
        {"quiz_id": "Q302", "skill_id": "120", "course": "MLOps Essentials", "last_score": 45, "pass_threshold": 60, "status": "failed"},
    ],
}

_QUIZ_ATTEMPTS: dict[str, list[dict]] = {
    "Q101": [
        {"course": "Learning FastAPI Fundamentals", "score": 82, "status": "passed", "attempted_on": "2026-06-29T07:25:00Z", "feedback": "Solid understanding of routing and dependency injection."},
        {"course": "Learning FastAPI Fundamentals", "score": 40, "status": "failed", "attempted_on": "2026-05-29T07:25:00Z", "feedback": "Need to go properly over endpoints and request validation."},
    ],
    "Q102": [
        {"course": "Learning Databases", "score": 40, "status": "failed", "attempted_on": "2026-05-20T07:25:00Z", "feedback": "Review indexing and normalization."},
    ],
    "Q201": [
        {"course": "Python Fundamentals", "score": 55, "status": "failed", "attempted_on": "2026-06-01T07:25:00Z", "feedback": "Revisit list/dict comprehensions and error handling."},
    ],
    "Q301": [
        {"course": "Statistics for ML", "score": 78, "status": "passed", "attempted_on": "2026-06-15T07:25:00Z", "feedback": "Good grasp of distributions and hypothesis testing."},
    ],
    "Q302": [
        {"course": "MLOps Essentials", "score": 45, "status": "failed", "attempted_on": "2026-06-20T07:25:00Z", "feedback": "Focus on CI/CD for models and monitoring next."},
    ],
}

_QUIZ_TO_EMPLOYEE: dict[str, str] = {
    quiz["quiz_id"]: uid for uid, quizzes in _QUIZ_CATALOG.items() for quiz in quizzes
}


def get_employee_quizzes(
    employee_id: str, limit: int = 20, offset: int = 0, search: str | None = None
) -> EmployeeQuizzesResponse:
    quizzes = _QUIZ_CATALOG.get(employee_id, [])
    if search:
        quizzes = [q for q in quizzes if search.lower() in q["course"].lower()]
    page, pagination = _paginate(quizzes, limit, offset)
    return EmployeeQuizzesResponse(
        employee_id=employee_id,
        quizzes=[QuizSummary(**q) for q in page],
        pagination=pagination,
    )


def get_quiz_attempts(quiz_id: str, limit: int = 20, offset: int = 0) -> QuizAttemptsResponse | None:
    employee_id = _QUIZ_TO_EMPLOYEE.get(quiz_id)
    if employee_id is None:
        return None
    attempts = _QUIZ_ATTEMPTS.get(quiz_id, [])
    attempts = sorted(attempts, key=lambda a: a["attempted_on"], reverse=True)
    page, pagination = _paginate(attempts, limit, offset)
    return QuizAttemptsResponse(
        employee_id=employee_id,
        quiz_id=quiz_id,
        attempts=[QuizAttempt(**a) for a in page],
        pagination=pagination,
    )


def get_employee_quiz_attempts(
    employee_id: str, limit: int = 20, offset: int = 0, search: str | None = None
) -> EmployeeQuizAttemptsResponse:
    rows: list[dict] = []
    for quiz in _QUIZ_CATALOG.get(employee_id, []):
        for attempt in _QUIZ_ATTEMPTS.get(quiz["quiz_id"], []):
            rows.append({
                "quiz_id": quiz["quiz_id"],
                "skill_id": quiz["skill_id"],
                "course": attempt["course"],
                "score": attempt["score"],
                "status": attempt["status"],
                "attempted_on": attempt["attempted_on"],
                "feedback": attempt["feedback"],
            })
    if search:
        needle = search.lower()
        rows = [r for r in rows if needle in r["course"].lower() or needle in r["skill_id"].lower()]
    rows.sort(key=lambda r: r["attempted_on"], reverse=True)
    page, pagination = _paginate(rows, limit, offset)
    return EmployeeQuizAttemptsResponse(
        employee_id=employee_id,
        attempts=[EmployeeQuizAttempt(**r) for r in page],
        pagination=pagination,
    )


# --------------------------------------------------------------------------
# Team 5 — composite dashboard views
# --------------------------------------------------------------------------


def get_employee_dashboard(employee_id: str) -> EmployeeDashboard:
    skill_profile = get_skill_detail(employee_id)
    roadmap = get_roadmap_by_employee_id(employee_id)
    quizzes = get_employee_quizzes(employee_id, limit=100, offset=0)
    recent_attempts = get_employee_quiz_attempts(employee_id, limit=100, offset=0)

    passed = sum(1 for q in quizzes.quizzes if q.status == "passed")
    pass_rate = round((passed / len(quizzes.quizzes)) * 100, 1) if quizzes.quizzes else 0.0

    return EmployeeDashboard(
        employee_id=employee_id,
        skill_profile=skill_profile,
        roadmap=roadmap,
        quizzes=quizzes,
        recent_quiz_attempts=recent_attempts,
        summary=EmployeeDashboardSummary(
            open_skill_gaps=len(skill_profile.skillGaps),
            roadmap_total_weeks=roadmap.plan.total_weeks if roadmap else None,
            total_quizzes=len(quizzes.quizzes),
            quiz_pass_rate_percentage=pass_rate,
        ),
    )


def get_team_members(manager_id: str) -> list[str]:
    return [uid for uid, e in _EMPLOYEES.items() if e["manager_id"] == manager_id]


def get_manager_dashboard(manager_id: str) -> ManagerDashboard:
    team = get_team_members(manager_id) or list(_EMPLOYEES.keys())

    training_completion = []
    certification_status = []
    for uid in team:
        e = _EMPLOYEES[uid]
        quizzes = _QUIZ_CATALOG.get(uid, [])
        passed = sum(1 for q in quizzes if q["status"] == "passed")
        training_completion.append(
            TrainingCompletionEntry(
                employee_id=uid,
                employee_name=e["name"],
                quizzes_passed=passed,
                quizzes_total=len(quizzes),
                completion_percentage=round((passed / len(quizzes)) * 100, 1) if quizzes else 0.0,
            )
        )
        certification_status.append(
            CertificationStatusEntry(
                employee_id=uid,
                employee_name=e["name"],
                role_alignment=e["role_alignment"],
                status="in_progress" if e["role_alignment"] != "ALIGNED" else "completed",
            )
        )

    return ManagerDashboard(
        manager_id=manager_id,
        team_size=len(team),
        team_skill_distribution=[
            TeamSkillDistributionEntry(skill_name="Python", employee_count=3, average_score=75.7),
            TeamSkillDistributionEntry(skill_name="FastAPI", employee_count=1, average_score=68.0),
            TeamSkillDistributionEntry(skill_name="AWS Cloud Architecture", employee_count=1, average_score=74.0),
        ],
        skill_gaps=[
            SkillGap(skill_name="FastAPI", required_level=90, current_average_level=55, gap=35, affected_employee_count=2),
            SkillGap(skill_name="MLOps", required_level=85, current_average_level=45, gap=40, affected_employee_count=1),
        ],
        training_completion=training_completion,
        certification_status=certification_status,
    )


def get_executive_dashboard() -> ExecutiveDashboard:
    return ExecutiveDashboard(
        org_ai_readiness_score=0.71,
        department_skills=[
            DepartmentSkillEntry(
                department="Backend & Cloud Engineering",
                average_ai_readiness_score=0.76,
                top_skill_gaps=["FastAPI", "Kubernetes"],
                headcount=2,
            ),
            DepartmentSkillEntry(
                department="Data & ML",
                average_ai_readiness_score=0.68,
                top_skill_gaps=["MLOps", "Model Evaluation"],
                headcount=1,
            ),
        ],
        training_roi=TrainingROI(
            total_training_hours=430.0,
            total_training_cost_usd=52000.0,
            estimated_productivity_gain_usd=118000.0,
            roi_percentage=126.9,
        ),
    )


# --------------------------------------------------------------------------
# Team 3 — AI tutor analytics (mirrors §4 of Team 3's contract exactly)
#
# NOTE: Team 3's payloads key off `user_id`. We key our mock dict by our
# own `employee_id` and treat them as equivalent, per the same gap Team 3
# themselves flagged in their doc (unconfirmed employee_id <-> user_id
# mapping). Swap for a real lookup once that's confirmed.
# --------------------------------------------------------------------------

_TUTOR_ENGAGEMENT: dict[str, dict] = {
    "usr_9823471": {
        "total_sessions": 5,
        "total_messages": 87,
        "total_questions_asked": 42,
        "total_documents_uploaded": 3,
        "avg_messages_per_session": 17.4,
        "grounded_response_rate": 0.82,
        "feedback_given": 28,
        "thumbs_up_rate": 0.89,
        "first_interaction": "2026-06-15T10:00:00Z",
        "last_interaction": "2026-07-09T12:30:00Z",
        "active_skills_count": 2,
        "completed_skills_count": 1,
    },
    "usr_9823472": {
        "total_sessions": 2,
        "total_messages": 21,
        "total_questions_asked": 10,
        "total_documents_uploaded": 0,
        "avg_messages_per_session": 10.5,
        "grounded_response_rate": 0.61,
        "feedback_given": 4,
        "thumbs_up_rate": 0.5,
        "first_interaction": "2026-06-20T09:00:00Z",
        "last_interaction": "2026-07-05T15:10:00Z",
        "active_skills_count": 1,
        "completed_skills_count": 0,
    },
    "usr_9823473": {
        "total_sessions": 4,
        "total_messages": 60,
        "total_questions_asked": 30,
        "total_documents_uploaded": 2,
        "avg_messages_per_session": 15.0,
        "grounded_response_rate": 0.77,
        "feedback_given": 18,
        "thumbs_up_rate": 0.83,
        "first_interaction": "2026-06-18T11:00:00Z",
        "last_interaction": "2026-07-08T08:45:00Z",
        "active_skills_count": 2,
        "completed_skills_count": 0,
    },
}

_TUTOR_SKILL_BREAKDOWN: dict[str, list[dict]] = {
    "usr_9823471": [
        {
            "skill_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "skill_name": "FastAPI",
            "skill_level": "intermediate",
            "target_role": "FastAPI Dev",
            "session_count": 3,
            "total_messages": 52,
            "total_questions": 24,
            "documents_uploaded": 2,
            "grounded_response_rate": 0.85,
            "thumbs_up_rate": 0.92,
            "last_interaction": "2026-07-09T12:30:00Z",
            "top_topics_asked": ["dependency injection", "request validation", "async routes"],
            "guardrail_blocks": 1,
        },
        {
            "skill_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "skill_name": "AWS Cloud Architecture",
            "skill_level": "beginner",
            "target_role": "FastAPI Dev",
            "session_count": 2,
            "total_messages": 35,
            "total_questions": 18,
            "documents_uploaded": 1,
            "grounded_response_rate": 0.78,
            "thumbs_up_rate": 0.86,
            "last_interaction": "2026-07-02T09:15:00Z",
            "top_topics_asked": ["IAM roles", "VPC basics"],
            "guardrail_blocks": 0,
        },
    ],
    "usr_9823472": [
        {
            "skill_id": "5b2e9e10-8b2a-4b3e-9f1a-1c2d3e4f5a6b",
            "skill_name": "Python",
            "skill_level": "beginner",
            "target_role": "Python Dev",
            "session_count": 2,
            "total_messages": 21,
            "total_questions": 10,
            "documents_uploaded": 0,
            "grounded_response_rate": 0.61,
            "thumbs_up_rate": 0.5,
            "last_interaction": "2026-07-05T15:10:00Z",
            "top_topics_asked": ["list comprehensions", "error handling"],
            "guardrail_blocks": 3,
        },
    ],
    "usr_9823473": [
        {
            "skill_id": "9c1d2e3f-4a5b-4c6d-8e7f-0a1b2c3d4e5f",
            "skill_name": "MLOps",
            "skill_level": "beginner",
            "target_role": "ML Engineer",
            "session_count": 2,
            "total_messages": 32,
            "total_questions": 15,
            "documents_uploaded": 1,
            "grounded_response_rate": 0.74,
            "thumbs_up_rate": 0.8,
            "last_interaction": "2026-07-08T08:45:00Z",
            "top_topics_asked": ["CI/CD for models", "model monitoring"],
            "guardrail_blocks": 1,
        },
        {
            "skill_id": "9c1d2e3f-4a5b-4c6d-8e7f-0a1b2c3d4e5f",
            "skill_name": "Statistics",
            "skill_level": "intermediate",
            "target_role": "ML Engineer",
            "session_count": 2,
            "total_messages": 28,
            "total_questions": 15,
            "documents_uploaded": 1,
            "grounded_response_rate": 0.8,
            "thumbs_up_rate": 0.86,
            "last_interaction": "2026-07-06T14:20:00Z",
            "top_topics_asked": ["hypothesis testing", "distributions"],
            "guardrail_blocks": 0,
        },
    ],
}


def get_employee_analytics_summary(employee_id: str) -> EmployeeAnalyticsSummary | None:
    row = _TUTOR_ENGAGEMENT.get(employee_id)
    if row is None:
        return None
    return EmployeeAnalyticsSummary(user_id=employee_id, **row)


def get_employee_skill_analytics(employee_id: str) -> EmployeeSkillAnalytics | None:
    rows = _TUTOR_SKILL_BREAKDOWN.get(employee_id)
    if rows is None:
        return None
    return EmployeeSkillAnalytics(
        user_id=employee_id,
        skills=[EmployeeSkillInteraction(**r) for r in rows],
    )


def get_tutor_analytics_overview(from_date: str, to_date: str) -> TutorAnalyticsOverview:
    return TutorAnalyticsOverview(
        period=TutorAnalyticsPeriod(**{"from": from_date, "to": to_date}),
        total_users=len(_EMPLOYEES),
        active_users=sum(1 for v in _TUTOR_ENGAGEMENT.values() if v["total_sessions"] > 0),
        total_sessions=sum(v["total_sessions"] for v in _TUTOR_ENGAGEMENT.values()),
        total_messages=sum(v["total_messages"] for v in _TUTOR_ENGAGEMENT.values()),
        avg_session_length_messages=15.0,
        grounded_response_rate=0.79,
        thumbs_up_rate=0.84,
        documents_uploaded=sum(v["total_documents_uploaded"] for v in _TUTOR_ENGAGEMENT.values()),
        guardrail_block_rate=0.06,
        top_skills=[
            TopSkillBySessionCount(skill_name="FastAPI", session_count=3),
            TopSkillBySessionCount(skill_name="MLOps", session_count=2),
            TopSkillBySessionCount(skill_name="Python", session_count=2),
        ],
        top_ungrounded_skills=[
            TopUngroundedSkill(skill_name="Python", grounded_rate=0.61),
        ],
    )