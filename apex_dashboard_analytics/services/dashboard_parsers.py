"""Parsers that normalize raw integration responses into dashboard sections.

Each parser takes the raw JSON returned by an integration method (see the
"Expected Response" blocks in the integration modules) and returns a clean,
predictable structure for the aggregated employee dashboard.

Parsers are intentionally *defensive*: upstream payloads may have missing keys,
nulls, or empty collections. A parser should degrade gracefully (returning
sensible defaults) rather than raise on shape drift.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any
from datetime import datetime

_PASSED = "passed"


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _numbers(values: Any) -> list[float]:
    return [
        v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]


# --------------------------------------------------------------------------- #
# Skill Profiler
# --------------------------------------------------------------------------- #
def parse_user_profile(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse GET /api/v1/me -> the dashboard ``employee`` block."""
    raw = raw or {}
    return {
        "id": raw.get("userId"),
        "name": raw.get("username"),
        "email": raw.get("email"),
        "designation": raw.get("role"),
        "manager": raw.get("reportsToName"),
        "managerId": raw.get("reportsTo"),
    }


def parse_skill_profile(raw: Any) -> dict[str, Any]:
    """Parse GET /api/v1/skill-analysis (a list) -> skill summary + charts.

    Uses the most recent record (by ``createdAt``) when multiple are returned.
    """
    records = _as_list(raw)
    if not records:
        return {
            "skills": {},
            "skillDistribution": [],
            "skillGaps": [],
            "currentSkillScore": None,
            "strongestSkill": None,
            "weakestSkill": None,
            "currentRole": None,
            "targetRole": None,
            "roleAlignment": None,
        }

    record = max(records, key=lambda r: (r or {}).get("createdAt") or "")
    record = record or {}

    skills: dict[str, Any] = record.get("skills") or {}
    scored = {
        k: v
        for k, v in skills.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }

    sorted_skills = sorted(
        skills.items(),
        key=lambda x: x[1] if isinstance(x[1], (int, float)) else -1,
        reverse=True,
    )
    distribution = [
        {"skill": name, "score": score * 10 if score < 10 else score}
        for name, score in sorted_skills[:5]
    ]

    skill_gaps_list = record.get("skillGaps")

    skill_gaps: dict = {
        skill.get("skill"): skill.get("requiredLevel") for skill in skill_gaps_list
    }

    sorted_gaps = sorted(
        skill_gaps.items(),
        key=lambda x: x[1] if isinstance(x[1], (int, float)) else -1,
        reverse=True,
    )
    gaps = [
        {
            "skill": skill,
            "requiredLevel": required_level * 10
            if required_level < 10
            else required_level,
        }
        for skill, required_level in sorted_gaps[:5]
    ]

    return {
        "skillId": record.get("skillId"),
        "currentRole": record.get("currentRole"),
        "targetRole": record.get("targetRole"),
        "roleAlignment": record.get("roleAlignment"),
        "skills": skills,
        "skillDistribution": distribution,
        "skillGaps": gaps,
        "currentSkillScore": round(mean(scored.values())) if scored else None,
        "strongestSkill": max(scored, key=scored.get) if scored else None,
        "weakestSkill": min(scored, key=scored.get) if scored else None,
    }


# --------------------------------------------------------------------------- #
# Assessment
# --------------------------------------------------------------------------- #


def _get_average_latest_score(attempts: list) -> int:
    # Dictionary to keep track of the latest attempt for each course
    latest_attempts = {}

    for attempt in attempts:
        course_id = attempt["course_id"]
        # Convert ISO timestamp string into a datetime object for comparison
        attempted_on = datetime.fromisoformat(
            attempt["attempted_on"].replace("Z", "+00:00")
        )

        # If course not seen yet or this attempt is newer, update the record
        if (
            course_id not in latest_attempts
            or attempted_on > latest_attempts[course_id]["attempted_on"]
        ):
            latest_attempts[course_id] = {
                "score": attempt["score"],
                "attempted_on": attempted_on,
                "status": attempt["status"],
            }

    latest_scores = [item.get("score", 0) for item in latest_attempts.values()]
    latest_passed_count = sum(
        1 for item in latest_attempts.values() if item.get("status") == "pass"
    )
    count = len(latest_attempts)
    learning_progress = round((latest_passed_count / count) * 100, 2) if count else 0.0

    raw_avg = sum(latest_scores) / len(latest_scores) if latest_scores else 0
    return {
        "quizAverage": round(raw_avg * 10, 1),
        "learning_progress": learning_progress,
    }


def parse_assessments(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the employee assessments response -> quiz summary + metrics."""
    raw = raw or {}
    items = _as_list(raw.get("assessments"))

    quizzes = [
        {
            "assessment_id": a.get("assessment_id"),
            "course_id": a.get("course_id"),
            "course": a.get("course"),
            "last_score": a.get("last_score"),
            "pass_threshold": a.get("pass_threshold"),
            "status": a.get("status"),
        }
        for a in items
        if isinstance(a, dict)
    ]

    scores = _numbers([q["last_score"] for q in quizzes])
    total = len(quizzes)
    passed = sum(1 for q in quizzes if str(q.get("status") or "").lower() == _PASSED)

    return {
        "quizzes": quizzes,
        "totalQuizzes": total,
        "quizzesPassed": passed,
        "quizAverage": round(mean(scores), 1) if scores else None,
        "quizPassRate": round(passed / total * 100, 1) if total else None,
    }


def parse_assessment_attempts(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the cross-assessment attempts response -> normalized attempts."""
    raw = raw or {}
    attempts = [
        {
            "assessment_id": a.get("assessment_id"),
            "course_id": a.get("course_id"),
            "course": a.get("course"),
            "score": a.get("score"),
            "status": a.get("status"),
            "attempted_on": a.get("attempted_on"),
            "feedback": a.get("feedback"),
        }
        for a in _as_list(raw.get("attempts"))
        if isinstance(a, dict)
    ]
    # Most recent first when timestamps are present.
    attempts.sort(key=lambda a: a.get("attempted_on") or "", reverse=True)
    passed_courses = {
        item["course_id"] for item in attempts if item.get("status") == "pass"
    }

    return {
        "attempts": attempts,
        "total": len(attempts),
        "certifications_earned": len(passed_courses),
        **_get_average_latest_score(attempts=attempts),
    }


# --------------------------------------------------------------------------- #
# AI Tutor
# --------------------------------------------------------------------------- #
def parse_tutor_summary(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the tutor user-summary response (engagement metrics)."""
    raw = raw or {}
    return {
        "totalSessions": raw.get("total_sessions", 0),
        "totalMessages": raw.get("total_messages", 0),
        "totalQuestionsAsked": raw.get("total_questions_asked", 0),
        "documentsUploaded": raw.get("total_documents_uploaded", 0),
        "avgMessagesPerSession": raw.get("avg_messages_per_session", 0),
        "groundedResponseRate": raw.get("grounded_response_rate", 0),
        "thumbsUpRate": raw.get("thumbs_up_rate", 0),
        "firstInteraction": raw.get("first_interaction"),
        "lastInteraction": raw.get("last_interaction"),
        "activeSkillsCount": raw.get("active_skills_count", 0),
        "completedSkillsCount": raw.get("completed_skills_count", 0),
    }


def parse_tutor_skills(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the tutor per-skill analytics response."""
    raw = raw or {}
    skills = [
        {
            "skillId": s.get("skill_id"),
            "skillName": s.get("skill_name"),
            "skillLevel": s.get("skill_level"),
            "targetRole": s.get("target_role"),
            "sessionCount": s.get("session_count", 0),
            "totalMessages": s.get("total_messages", 0),
            "totalQuestions": s.get("total_questions", 0),
            "documentsUploaded": s.get("documents_uploaded", 0),
            "groundedResponseRate": s.get("grounded_response_rate", 0),
            "thumbsUpRate": s.get("thumbs_up_rate", 0),
            "lastInteraction": s.get("last_interaction"),
            "topTopicsAsked": _as_list(s.get("top_topics_asked")),
            "guardrailBlocks": s.get("guardrail_blocks", 0),
        }
        for s in _as_list(raw.get("skills"))
        if isinstance(s, dict)
    ]
    return {"skills": skills, "activeSkillsCount": len(skills)}


# --------------------------------------------------------------------------- #
# Learning Assistant
# --------------------------------------------------------------------------- #
def parse_courses(roadmaps: Any) -> list[dict[str, Any]]:
    """Flatten roadmap weeks into a de-duplicated list of courses."""
    courses: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for roadmap in _as_list(roadmaps):
        if not isinstance(roadmap, dict):
            continue
        for week in _as_list((roadmap.get("plan") or {}).get("weeks")):
            if not isinstance(week, dict):
                continue
            for course in _as_list(week.get("courses")):
                if not isinstance(course, dict):
                    continue
                key = (course.get("course_name"), course.get("url"))
                if key in seen:
                    continue
                seen.add(key)
                courses.append(
                    {
                        "course_name": course.get("course_name"),
                        "provider": course.get("provider"),
                        "url": course.get("url"),
                    }
                )
    return courses


def _week_completed(week: dict[str, Any]) -> bool:
    status = str(week.get("status") or "").lower()
    return status in {"completed", "done"} or bool(week.get("completed"))


def _week_has_completion(week: dict[str, Any]) -> bool:
    return "status" in week or "completed" in week


def parse_roadmap(raw: Any) -> dict[str, Any]:
    """Parse the employee roadmaps response -> the ``roadmap`` summary block.

    Only values present in the response are reported. ``totalWeeks`` comes from
    the plan; completion fields are populated *only* when the weeks actually
    carry completion info (``status``/``completed``), otherwise they are None.
    ``nextFocus`` is the focus of the first not-completed week, or None.
    """
    empty = {
        "totalWeeks": None,
        "completedWeeks": None,
        "completionPercentage": None,
        "currentWeek": None,
        "nextFocus": None,
        "course_recommendations": [],
    }
    roadmaps = [r for r in _as_list(raw) if isinstance(r, dict)]
    if not roadmaps:
        return empty

    roadmap = max(roadmaps, key=lambda r: r.get("created_at") or "")
    plan = roadmap.get("plan") or {}
    weeks = [w for w in _as_list(plan.get("weeks")) if isinstance(w, dict)]

    total = plan.get("total_weeks")
    if total is None and weeks:
        total = len(weeks)

    # Completion info is only reported when the response provides it.
    # has_completion = any(_week_has_completion(w) for w in weeks)
    # if not has_completion:
    #     return {**empty, "totalWeeks": total}

    completed = sum(1 for w in weeks if _week_completed(w))
    current = min(completed + 1, total) if total else None
    next_focus = None
    for w in weeks:
        if not _week_completed(w):
            next_focus = w.get("focus")
            break
    all_courses = []

    for week in weeks:
        for course in week.get("courses", []):
            all_courses.append(
                {
                    "course_name": course.get("course_name"),
                    "provider": course.get("provider"),
                    # "description": course.get("url"),
                }
            )

    return {
        "totalWeeks": total,
        "completedWeeks": completed,
        "completionPercentage": round(completed / total * 100) if total else None,
        "currentWeek": current,
        "nextFocus": next_focus,
        "course_recommendations": all_courses,
    }


# --------------------------------------------------------------------------- #
# Assembler -> single-employee shape (matches data/employees.json)
# --------------------------------------------------------------------------- #
_EMPTY_ROADMAP = {
    "totalWeeks": None,
    "completedWeeks": None,
    "completionPercentage": None,
    "currentWeek": None,
    "nextFocus": None,
}


def assemble_employee_dashboard(
    employee_id: str,
    *,
    user_profile: dict[str, Any] | None,
    skill_profile: dict[str, Any] | None,
    assessments: dict[str, Any] | None,
    roadmap: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge parsed sections into the single-employee ``employees.json`` shape.

    Every value is taken from an upstream response (via the ``parse_*``
    functions). Nothing is fabricated: fields with no corresponding response
    attribute are ``None`` (scalars) or ``[]`` (lists). Missing/failed sections
    are tolerated, so the returned structure is always complete.
    """
    up = user_profile or {}
    sp = skill_profile or {}
    asmt = assessments or {}
    rd = roadmap or {}

    return {
        "employee": {
            "id": up.get("id") or employee_id,
            "name": up.get("name"),
            "designation": up.get("designation") or sp.get("currentRole"),
            "department": up.get("department"),
            "manager": up.get("manager"),
        },
        "summary": {
            "currentSkillScore": sp.get("currentSkillScore"),
            "learningProgress": asmt.get("learning_progress"),
            "quizAverage": asmt.get("quizAverage"),
            "certificationsEarned": asmt.get("certifications_earned"),
        },
        "charts": {
            # No time-series in any upstream response yet.
            "skillTrend": [],
            "skillDistribution": sp.get("skillDistribution") or [],
            "skillGaps": sp.get("skillGaps"),
        },
        "course_recommendations": rd.get("course_recommendations", []),
        "analytics": {
            "strongestSkill": sp.get("strongestSkill"),
            "weakestSkill": sp.get("weakestSkill"),
            "quizPassRate": asmt.get("quizAverage"),
        },
        "roadmap": roadmap or dict(_EMPTY_ROADMAP),
    }


# --------------------------------------------------------------------------- #
# Manager dashboard
# --------------------------------------------------------------------------- #
def parse_manager_profile(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the manager's own profile (SkillProfiler /me) -> manager block."""
    raw = raw or {}
    return {
        "id": raw.get("userId"),
        "name": raw.get("username"),
        # /me does not expose department; None until an upstream provides it.
        "department": raw.get("department"),
    }


def parse_manager_team(raw: Any) -> list[dict[str, Any]]:
    """Parse the manager's team list (SkillProfiler /api/v1/users) -> member summaries.

    The /api/v1/users response is a list of users with basic info.
    We map what's available; fields not provided by the upstream are left as None.
    """
    team = _as_list(raw)
    members = []
    for user in team:
        if not isinstance(user, dict):
            continue
        members.append(
            {
                "employeeId": user.get("userId"),
                "name": user.get("username"),
                # The team endpoint does not provide these; they would need per-employee detail calls.
                "skillScore": None,
                "learningProgress": None,
                "skills": {},
                "skillGaps": [],
                "quizAverage": None,
                "quizPassRate": None,
                "certificationRatio": None,
            }
        )
    return members


def parse_member_summary(
    *,
    employee_id: str | None,
    name: str | None,
    skill_profile: dict[str, Any] | None = None,
    assessments: dict[str, Any] | None = None,
    roadmap: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a single team-member summary from per-employee detail calls.

    Fields that the upstream does not provide are left as None.
    """
    sp = skill_profile or {}
    asmt = assessments or {}
    lp = None
    if roadmap:
        lp = roadmap.get("completionPercentage")
    return {
        "employeeId": employee_id,
        "name": name,
        "skillScore": sp.get("currentSkillScore"),
        "learningProgress": lp,
        "skills": sp.get("skills") or {},
        "skillGaps": sp.get("skillGaps") or [],
        "quizAverage": asmt.get("quizAverage"),
        "quizPassRate": asmt.get("quizPassRate"),
        "certificationRatio": asmt.get("certificationRatio"),
    }


def _team_skill_distribution(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for member in members:
        for skill in member.get("skills") or {}:
            counter[skill] += 1
    return [
        {"skill": skill, "employees": count} for skill, count in counter.most_common()
    ]


def _team_skill_gaps(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for member in members:
        for gap in member.get("skillGaps") or []:
            skill = gap.get("skill") if isinstance(gap, dict) else None
            if skill:
                counter[skill] += 1
    return [
        {"skill": skill, "employeesAffected": count}
        for skill, count in counter.most_common()
    ]


def assemble_manager_dashboard(
    manager_id: str,
    *,
    manager: dict[str, Any] | None,
    members: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the ``managers.json`` shape.

    ``members`` is a list of parsed per-employee summaries (each optionally
    carrying ``employeeId``, ``name``, ``skillScore``, ``learningProgress``,
    ``skills``, ``skillGaps``, ``quizAverage``, ``quizPassRate``,
    ``certificationRatio``). Team rollups are computed only from this
    response-derived data; when no members are available the team sections are
    ``[]`` / ``None`` (nothing fabricated).
    """
    m = manager or {}
    members = [x for x in (members or []) if isinstance(x, dict)]

    skill_scores = _numbers([x.get("skillScore") for x in members])
    progress = _numbers([x.get("learningProgress") for x in members])
    quiz_avgs = _numbers([x.get("quizAverage") for x in members])
    pass_rates = _numbers([x.get("quizAverage") for x in members])
    cert_ratios = _numbers([x.get("certificationRatio") for x in members])

    scored = [x for x in members if isinstance(x.get("skillScore"), (int, float))]
    top = max(scored, key=lambda x: x["skillScore"], default=None)
    low = min(scored, key=lambda x: x["skillScore"], default=None)

    return {
        "manager": {
            "id": m.get("id") or manager_id,
            "name": m.get("name"),
            "department": m.get("department"),
        },
        "summary": {
            "teamSize": len(members) if members else None,
            "averageSkillScore": round(mean(skill_scores)) if skill_scores else None,
            "averageLearningProgress": round(mean(progress)) if progress else None,
            "pendingTrainings": (
                sum(len(x.get("skillGaps") or []) for x in members) if members else None
            ),
            "certificationCompletion": (
                round(mean(cert_ratios) * 100) if cert_ratios else None
            ),
        },
        "charts": {"teamSkillDistribution": _team_skill_distribution(members)},
        "skillGaps": _team_skill_gaps(members),
        "teamMembers": [
            {
                "employeeId": x.get("employeeId"),
                "name": x.get("name"),
                "skillScore": x.get("skillScore"),
                "learningProgress": x.get("learningProgress"),
            }
            for x in members
        ],
        "analytics": {
            "topPerformer": top.get("name") if top else None,
            "lowestPerformer": low.get("name") if low else None,
            "trainingCompletionRate": round(mean(pass_rates)) if pass_rates else None,
            "averageQuizScore": round(mean(quiz_avgs), 1) if quiz_avgs else None,
        },
    }


# --------------------------------------------------------------------------- #
# Executive dashboard
# --------------------------------------------------------------------------- #
def parse_org_overview(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Parse the AI Tutor org overview response (defensive passthrough).

    Kept as a light passthrough: the executive assembler pulls the fields it
    recognizes and defaults the rest, so new overview fields flow through
    without code changes.
    """
    return raw or {}


def _department_analytics(departments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "department": d.get("department"),
            "employees": d.get("employees"),
            "avgSkillScore": d.get("avgSkillScore"),
            "completion": d.get("completion"),
        }
        for d in departments
    ]


def assemble_executive_dashboard(
    *,
    name: str | None = None,
    overview: dict[str, Any] | None = None,
    departments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the ``executive.json`` shape.

    ``departments`` is a list of response-derived per-department rollups (each
    optionally carrying ``department``, ``employees``, ``avgSkillScore``,
    ``completion``, ``readinessScore``). Fields with no upstream source are
    ``None`` / ``[]`` (nothing fabricated).
    """
    overview = overview or {}
    departments = [d for d in (departments or []) if isinstance(d, dict)]

    dept_scores = _numbers([d.get("avgSkillScore") for d in departments])
    scored = [
        d for d in departments if isinstance(d.get("avgSkillScore"), (int, float))
    ]
    highest = max(scored, key=lambda d: d["avgSkillScore"], default=None)
    lowest = min(scored, key=lambda d: d["avgSkillScore"], default=None)

    return {
        "Executive": {
            "departments": len(departments) if departments else None,
        },
        "summary": {
            "overallAIReadiness": overview.get("overall_ai_readiness"),
            "overallLearningCompletion": overview.get("overall_learning_completion"),
            "trainingROI": overview.get("training_roi"),
            "trainingCost": overview.get("training_cost"),
            "certificationRate": overview.get("certification_rate"),
            "averageSkillScore": round(mean(dept_scores)) if dept_scores else None,
        },
        "charts": {
            "departmentReadiness": [
                {"department": d.get("department"), "score": d.get("readinessScore")}
                for d in departments
                if d.get("readinessScore") is not None
            ],
            # No monthly time-series in any upstream response yet.
            "monthlyAIReadinessTrend": [],
        },
        "departmentAnalytics": _department_analytics(departments),
        "analytics": {
            "highestPerformingDepartment": (
                highest.get("department") if highest else None
            ),
            "lowestPerformingDepartment": lowest.get("department") if lowest else None,
        },
        "top_skills": overview.get("top_skills"),
        "top_ungrounded_skills": overview.get("top_ungrounded_skills"),
    }
