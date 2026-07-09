from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import structlog

from apex_dashboard_analytics.schemas import (
    SkillDetailResponse,
    SkillGapItem,
    Roadmap,
    RoadmapCourse,
    RoadmapPlan,
    RoadmapWeek,
    EmployeeQuizzesResponse,
    QuizSummary,
    Pagination,
    EmployeeQuizAttemptsResponse,
    EmployeeQuizAttempt,
    QuizAttemptsResponse,
    QuizAttempt,
    EmployeeDashboard,
    EmployeeDashboardSummary,
    ManagerDashboard,
    TeamSkillDistributionEntry,
    SkillGap,
    TrainingCompletionEntry,
    CertificationStatusEntry,
    ExecutiveDashboard,
    DepartmentSkillEntry,
    TrainingROI,
)
from apex_dashboard_analytics.schemas.tutoring import (
    UserAnalyticsSummary,
    UserSkillsBreakdown,
    UserSkillInteraction,
    TutorOverviewResponse,
    TutorOverviewPeriod,
    TopSkillUsage,
    TopUngroundedSkill,
    QuizResultWebhookPayload,
)

logger = structlog.get_logger(__name__)

# --- In-Memory Mock Datastore ---

# Supported employees
_EMPLOYEES = {
    "550e8400-e29b-41d4-a716-446655440000": {
        "username": "john_doe",
        "email": "john.doe@apex.com",
        "current_role": "Python Developer",
        "target_role": "FastAPI Developer",
    },
    "usr_9823471": {
        "username": "jane_smith",
        "email": "jane.smith@apex.com",
        "current_role": "Junior Developer",
        "target_role": "Backend Engineer",
    }
}

# Webhook quiz attempts received from Team 4
_RECEIVED_WEBHOOK_QUIZZES: list[QuizResultWebhookPayload] = []


def employee_exists(employee_id: str) -> bool:
    return employee_id in _EMPLOYEES


def get_skill_detail(employee_id: str) -> SkillDetailResponse:
    emp = _EMPLOYEES.get(employee_id, {
        "username": "guest_user",
        "email": "guest@apex.com",
        "current_role": "Developer",
        "target_role": "Senior Developer",
    })
    return SkillDetailResponse(
        skillId="sk_python",
        userId=employee_id,
        username=emp["username"],
        email=emp["email"],
        currentRole=emp["current_role"],
        targetRole=emp["target_role"],
        skills={
            "Python": 0.85,
            "FastAPI": 0.60,
            "SQL": 0.70
        },
        skillGaps=[
            SkillGapItem(skill="Asyncio", requiredLevel=4),
            SkillGapItem(skill="Dependency Injection", requiredLevel=3)
        ],
        roleAlignment="ALIGNED",
        status="COMPLETED",
        createdAt=datetime(2026, 6, 29, 7, 25, 0, tzinfo=timezone.utc),
    )


def get_roadmap_by_employee_id(employee_id: str) -> Roadmap | None:
    return Roadmap(
        roadmap_id="rm_1001",
        skill_id="sk_python",
        target_role="FastAPI Developer",
        status="in_progress",
        plan=RoadmapPlan(
            summary="Mastering web services using FastAPI in Python",
            total_weeks=4,
            weeks=[
                RoadmapWeek(
                    week=1,
                    focus="Python Advanced Concepts",
                    skills=["Asyncio", "Type Hints"],
                    courses=[
                        RoadmapCourse(
                            course_id="c_adv_py",
                            course_name="Advanced Python Foundations",
                            provider="Internal Academy",
                            url="http://academy.apex.com/courses/adv-py",
                            duration_hours=6.5,
                            skills_taught=["Asyncio", "Generators"]
                        )
                    ],
                    activities=["Code async web scraper", "Refactor codebase with type hints"]
                ),
                RoadmapWeek(
                    week=2,
                    focus="FastAPI Basics",
                    skills=["FastAPI Routing", "Pydantic"],
                    courses=[
                        RoadmapCourse(
                            course_id="c_fastapi_fundamentals",
                            course_name="Learning FastAPI Fundamentals",
                            provider="Pluralsight",
                            url="https://pluralsight.com/fastapi-basics",
                            duration_hours=10.0,
                            skills_taught=["FastAPI Routing", "Pydantic"]
                        )
                    ],
                    activities=["Setup first fastapi endpoints", "Write pydantic models for validation"]
                )
            ]
        ),
        created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
    )


def get_roadmap_by_skill_id(skill_id: str) -> Roadmap | None:
    # Just return a generic roadmap for the skill
    return get_roadmap_by_employee_id("550e8400-e29b-41d4-a716-446655440000")


def get_employee_quizzes(employee_id: str, limit: int = 20, offset: int = 0, search: str | None = None) -> EmployeeQuizzesResponse:
    quizzes = [
        QuizSummary(
            quiz_id="Q101",
            skill_id="sk_fastapi",
            course="Learning FastAPI Fundamentals",
            last_score=40,
            pass_threshold=60,
            status="failed"
        ),
        QuizSummary(
            quiz_id="Q102",
            skill_id="sk_python",
            course="Advanced Python Foundations",
            last_score=85,
            pass_threshold=60,
            status="passed"
        )
    ]
    
    # Simple search filter
    if search:
        quizzes = [q for q in quizzes if search.lower() in q.course.lower()]
        
    total = len(quizzes)
    sliced_quizzes = quizzes[offset : offset + limit]
    
    return EmployeeQuizzesResponse(
        employee_id=employee_id,
        quizzes=sliced_quizzes,
        pagination=Pagination(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + limit) < total
        )
    )


def get_employee_quiz_attempts(employee_id: str, limit: int = 20, offset: int = 0, search: str | None = None) -> EmployeeQuizAttemptsResponse:
    attempts = [
        EmployeeQuizAttempt(
            quiz_id="Q101",
            skill_id="sk_fastapi",
            course="Learning FastAPI Fundamentals",
            score=40,
            status="failed",
            attempted_on=datetime(2026, 7, 9, 7, 25, 0, tzinfo=timezone.utc),
            feedback="Need to review endpoints and request validation."
        ),
        EmployeeQuizAttempt(
            quiz_id="Q102",
            skill_id="sk_python",
            course="Advanced Python Foundations",
            score=85,
            status="passed",
            attempted_on=datetime(2026, 7, 8, 14, 30, 0, tzinfo=timezone.utc),
            feedback="Excellent grasp of core programming decorators."
        )
    ]
    
    # Add any webhook attempts dynamically
    for item in _RECEIVED_WEBHOOK_QUIZZES:
        if item.user_id == employee_id:
            attempts.insert(0, EmployeeQuizAttempt(
                quiz_id=item.quiz_id,
                skill_id=item.skill_id,
                course=item.course,
                score=item.score,
                status="passed" if item.score >= item.pass_threshold else "failed",
                attempted_on=item.attempted_on,
                feedback=item.feedback
            ))
            
    if search:
        attempts = [a for a in attempts if search.lower() in a.course.lower()]
        
    total = len(attempts)
    sliced_attempts = attempts[offset : offset + limit]
    
    return EmployeeQuizAttemptsResponse(
        employee_id=employee_id,
        attempts=sliced_attempts,
        pagination=Pagination(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + limit) < total
        )
    )


def get_quiz_attempts(quiz_id: str, limit: int = 20, offset: int = 0) -> QuizAttemptsResponse | None:
    attempts = [
        QuizAttempt(
            course="Learning FastAPI Fundamentals" if quiz_id == "Q101" else "Advanced Python Foundations",
            score=40 if quiz_id == "Q101" else 85,
            status="failed" if quiz_id == "Q101" else "passed",
            attempted_on=datetime(2026, 7, 9, 7, 25, 0, tzinfo=timezone.utc),
            feedback="Review dependency injection."
        )
    ]
    
    total = len(attempts)
    return QuizAttemptsResponse(
        employee_id="550e8400-e29b-41d4-a716-446655440000",
        quiz_id=quiz_id,
        attempts=attempts,
        pagination=Pagination(
            limit=limit,
            offset=offset,
            total=total,
            has_more=(offset + limit) < total
        )
    )


def get_employee_dashboard(employee_id: str) -> EmployeeDashboard:
    profile = get_skill_detail(employee_id)
    roadmap = get_roadmap_by_employee_id(employee_id)
    quizzes = get_employee_quizzes(employee_id)
    attempts = get_employee_quiz_attempts(employee_id)
    
    return EmployeeDashboard(
        employee_id=employee_id,
        skill_profile=profile,
        roadmap=roadmap,
        quizzes=quizzes,
        recent_quiz_attempts=attempts,
        summary=EmployeeDashboardSummary(
            open_skill_gaps=len(profile.skillGaps),
            roadmap_total_weeks=roadmap.plan.total_weeks if roadmap else 0,
            total_quizzes=len(quizzes.quizzes),
            quiz_pass_rate_percentage=50.0
        )
    )


def get_manager_dashboard(manager_id: str) -> ManagerDashboard:
    return ManagerDashboard(
        manager_id=manager_id,
        team_size=2,
        team_skill_distribution=[
            TeamSkillDistributionEntry(skill_name="Python", employee_count=2, average_score=0.85),
            TeamSkillDistributionEntry(skill_name="FastAPI", employee_count=1, average_score=0.60)
        ],
        skill_gaps=[
            SkillGap(
                skill_name="Asyncio",
                required_level=4.0,
                current_average_level=2.5,
                gap=1.5,
                affected_employee_count=2
            )
        ],
        training_completion=[
            TrainingCompletionEntry(
                employee_id="550e8400-e29b-41d4-a716-446655440000",
                employee_name="John Doe",
                quizzes_passed=1,
                quizzes_total=2,
                completion_percentage=50.0
            )
        ],
        certification_status=[
            CertificationStatusEntry(
                employee_id="550e8400-e29b-41d4-a716-446655440000",
                employee_name="John Doe",
                role_alignment="ALIGNED",
                status="in_progress"
            )
        ]
    )


def get_executive_dashboard() -> ExecutiveDashboard:
    return ExecutiveDashboard(
        org_ai_readiness_score=0.78,
        department_skills=[
            DepartmentSkillEntry(
                department="Engineering",
                average_ai_readiness_score=0.82,
                top_skill_gaps=["Asyncio", "RAG Design Patterns"],
                headcount=20
            ),
            DepartmentSkillEntry(
                department="Product Management",
                average_ai_readiness_score=0.65,
                top_skill_gaps=["AI Roadmap Scoping"],
                headcount=5
            )
        ],
        training_roi=TrainingROI(
            total_training_hours=240.0,
            total_training_cost_usd=1200.0,
            estimated_productivity_gain_usd=4500.0,
            roi_percentage=275.0
        )
    )


# --- Team 3 (AI Tutor) Mock Implementation ---

def get_tutor_summary(user_id: str) -> UserAnalyticsSummary:
    return UserAnalyticsSummary(
        user_id=user_id,
        total_sessions=5,
        total_messages=87,
        total_questions_asked=42,
        total_documents_uploaded=3,
        avg_messages_per_session=17.4,
        grounded_response_rate=0.82,
        feedback_given=28,
        thumbs_up_rate=0.89,
        first_interaction=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        last_interaction=datetime(2026, 7, 9, 12, 30, 0, tzinfo=timezone.utc),
        active_skills_count=3,
        completed_skills_count=1
    )


def get_tutor_skills(user_id: str) -> UserSkillsBreakdown:
    return UserSkillsBreakdown(
        user_id=user_id,
        skills=[
            UserSkillInteraction(
                skill_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
                skill_name="System Design",
                skill_level="beginner",
                target_role="AI Engineer",
                session_count=2,
                total_messages=34,
                total_questions=16,
                documents_uploaded=2,
                grounded_response_rate=0.85,
                thumbs_up_rate=0.92,
                last_interaction=datetime(2026, 7, 9, 12, 30, 0, tzinfo=timezone.utc),
                top_topics_asked=["CAP theorem", "load balancing", "database sharding"],
                guardrail_blocks=2
            )
        ]
    )


def get_tutor_overview(from_date: str | None = None, to_date: str | None = None) -> TutorOverviewResponse:
    return TutorOverviewResponse(
        period=TutorOverviewPeriod(
            from_date=from_date or "2026-06-09",
            to_date=to_date or "2026-07-09"
        ),
        total_users=45,
        active_users=28,
        total_sessions=156,
        total_messages=2340,
        avg_session_length_messages=15,
        grounded_response_rate=0.79,
        thumbs_up_rate=0.84,
        documents_uploaded=67,
        guardrail_block_rate=0.06,
        top_skills=[
            TopSkillUsage(skill_name="System Design", session_count=42),
            TopSkillUsage(skill_name="Prompt Engineering", session_count=38),
            TopSkillUsage(skill_name="RAG Systems", session_count=31)
        ],
        top_ungrounded_skills=[
            TopUngroundedSkill(skill_name="Agentic AI", grounded_rate=0.45)
        ]
    )


def add_quiz_result(payload: QuizResultWebhookPayload) -> dict[str, Any]:
    logger.info(
        "quiz_result_webhook_received",
        user_id=payload.user_id,
        skill_id=payload.skill_id,
        quiz_id=payload.quiz_id,
        score=payload.score,
        status=payload.status,
    )
    _RECEIVED_WEBHOOK_QUIZZES.append(payload)
    return {"status": "received", "session_updated": True}
