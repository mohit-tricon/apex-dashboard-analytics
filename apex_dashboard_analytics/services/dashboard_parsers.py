"""Parsers that normalize raw integration responses into dashboard sections.

Each parser takes the raw JSON returned by an integration method (see the
"Expected Response" blocks in the integration modules) and returns a clean,
predictable structure for the aggregated employee dashboard.

Parsers are intentionally *defensive*: upstream payloads may have missing keys,
nulls, or empty collections. A parser should degrade gracefully (returning
sensible defaults) rather than raise on shape drift.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

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

    distribution = [{"skill": name, "score": score} for name, score in skills.items()]
    gaps = [
        {"skill": g.get("skill"), "requiredLevel": g.get("requiredLevel")}
        for g in _as_list(record.get("skillGaps"))
        if isinstance(g, dict)
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
    return {"attempts": attempts, "total": len(attempts)}


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
    has_completion = any(_week_has_completion(w) for w in weeks)
    if not has_completion:
        return {**empty, "totalWeeks": total}

    completed = sum(1 for w in weeks if _week_completed(w))
    current = min(completed + 1, total) if total else None
    next_focus = None
    for w in weeks:
        if not _week_completed(w):
            next_focus = w.get("focus")
            break

    return {
        "totalWeeks": total,
        "completedWeeks": completed,
        "completionPercentage": round(completed / total * 100) if total else None,
        "currentWeek": current,
        "nextFocus": next_focus,
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

    return {
        "employee": {
            "id": up.get("id") or employee_id,
            "name": up.get("name"),
            "designation": up.get("designation") or sp.get("currentRole"),
            "department": up.get("department"),
            "manager": up.get("manager"),
        },
        "summary": {
            # Derived only from response values (no invented constants).
            "currentSkillScore": sp.get("currentSkillScore"),
            # No response attribute for learning progress yet.
            "learningProgress": None,
            "quizAverage": asmt.get("quizAverage"),
            # No response attribute for certifications yet.
            "certificationsEarned": None,
        },
        "charts": {
            # No time-series in any upstream response yet.
            "skillTrend": [],
            "skillDistribution": sp.get("skillDistribution") or [],
        },
        # No recommendations response wired yet.
        "course_recommendations": [],
        "analytics": {
            "strongestSkill": sp.get("strongestSkill"),
            "weakestSkill": sp.get("weakestSkill"),
            "quizPassRate": asmt.get("quizPassRate"),
        },
        "roadmap": roadmap or dict(_EMPTY_ROADMAP),
    }
