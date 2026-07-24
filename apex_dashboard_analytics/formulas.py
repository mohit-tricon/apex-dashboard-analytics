"""Documentation of all formulas used in dashboard parsing and assembly.

Each entry describes the source function, the output field, the formula,
and whether the field accepts None when data is unavailable.
"""

from __future__ import annotations

from typing import Any

FORMULAS: dict[str, Any] = {
    "employee_dashboard": {
        "description": "Employee dashboard computed fields",
        "parsers": {
            "parse_skill_profile": {
                "source": "SkillProfiler GET /api/v1/skill-analysis",
                "fields": [
                    {
                        "field": "currentSkillScore",
                        "formula": "round(mean([score for skill, score in skills.items() if score is numeric]))",
                        "nullable": True,
                        "example": "skills={python: 8, java: 7, sql: 6} → round(mean([8,7,6])) = 7",
                    },
                    {
                        "field": "strongestSkill",
                        "formula": "max(skills, key=lambda s: skills[s])  → skill name with highest score",
                        "nullable": True,
                        "example": "skills={python: 8, java: 7} → 'python'",
                    },
                    {
                        "field": "weakestSkill",
                        "formula": "min(skills, key=lambda s: skills[s])  → skill name with lowest score",
                        "nullable": True,
                        "example": "skills={python: 8, java: 7} → 'java'",
                    },
                    {
                        "field": "skillDistribution",
                        "formula": (
                            "1. Sort skills by score descending\n"
                            "2. Take top 5\n"
                            "3. Normalize score: score * 10 if score < 10 else score"
                        ),
                        "nullable": False,
                        "example": "python:8, java:7, sql:6 → [{skill:'python', score:8}, {skill:'java', score:7}, {skill:'sql', score:6}]",
                    },
                    {
                        "field": "skillGaps",
                        "formula": (
                            "1. Group gaps by skill name (deduplicate)\n"
                            "2. Sort by requiredLevel descending\n"
                            "3. Take top 5\n"
                            "4. Normalize: requiredLevel * 10 if requiredLevel < 10 else requiredLevel"
                        ),
                        "nullable": False,
                        "example": "gaps: [{skill:'kubernetes', requiredLevel:8}, {skill:'aws', requiredLevel:6}] → [{skill:'kubernetes', requiredLevel:80}, {skill:'aws', requiredLevel:60}]",
                    },
                ],
            },
            "parse_assessments": {
                "source": "Assessment GET /api/v1/employees/{id}/quizzes",
                "fields": [
                    {
                        "field": "quizAverage",
                        "formula": "round(mean([q.last_score for q in quizzes]), 1)",
                        "nullable": True,
                        "example": "scores=[8, 7, 9] → round(mean([8,7,9]), 1) = 8.0",
                    },
                    {
                        "field": "quizPassRate",
                        "formula": "round((passed_count / total_quizzes) * 100, 1)",
                        "nullable": True,
                        "example": "passed=3, total=4 → round((3/4)*100, 1) = 75.0",
                    },
                    {
                        "field": "totalQuizzes",
                        "formula": "len(quizzes)",
                        "nullable": False,
                        "example": "5 quizzes → 5",
                    },
                    {
                        "field": "quizzesPassed",
                        "formula": "count of quizzes where status == 'passed' (case-insensitive)",
                        "nullable": False,
                        "example": "3 quizzes with status='passed' → 3",
                    },
                ],
            },
            "parse_assessment_attempts._get_average_latest_score": {
                "source": "Assessment GET /api/v1/employees/{id}/quiz-attempts",
                "fields": [
                    {
                        "field": "quizAverage (from attempts)",
                        "formula": "round(mean([latest_score for each course]) * 10, 1)",
                        "note": "Uses only the LATEST attempt per course. Raw score (0-10) is scaled to 0-100.",
                        "nullable": False,
                        "example": "course_A latest=8, course_B latest=7 → round(mean([8,7])*10, 1) = 75.0",
                    },
                    {
                        "field": "learning_progress",
                        "formula": "round((courses_passed_on_latest_attempt / total_unique_courses) * 100, 2)",
                        "nullable": False,
                        "example": "3 courses, 2 passed on latest attempt → round((2/3)*100, 2) = 66.67",
                    },
                    {
                        "field": "certifications_earned",
                        "formula": "len(unique course_ids where ANY attempt status == 'pass')",
                        "nullable": False,
                        "example": "attempts for 3 courses, all have at least one 'pass' → 3",
                    },
                ],
            },
            "parse_roadmap": {
                "source": "LearningAssistant GET /api/v1/employees/{id}/roadmap",
                "fields": [
                    {
                        "field": "totalWeeks",
                        "formula": "plan.total_weeks if present, else len(weeks)",
                        "nullable": True,
                        "example": "plan has total_weeks=12 → 12",
                    },
                    {
                        "field": "completedWeeks",
                        "formula": "count of weeks where status in {'completed', 'done'} or week.completed is truthy",
                        "nullable": False,
                        "example": "5 of 12 weeks completed → 5",
                    },
                    {
                        "field": "completionPercentage",
                        "formula": "round((completedWeeks / totalWeeks) * 100)",
                        "nullable": True,
                        "example": "5/12 completed → round((5/12)*100) = 42",
                    },
                    {
                        "field": "currentWeek",
                        "formula": "min(completedWeeks + 1, totalWeeks)",
                        "nullable": True,
                        "example": "5 completed, 12 total → min(5+1, 12) = 6",
                    },
                    {
                        "field": "nextFocus",
                        "formula": "focus field of the first week that is NOT completed (None if all complete)",
                        "nullable": True,
                        "example": "week 6 focus='Kubernetes' → 'Kubernetes'",
                    },
                ],
            },
        },
        "assembly": {
            "assemble_employee_dashboard": {
                "description": "Merges all parsed sections into the final employee dashboard payload",
                "field_mappings": [
                    {
                        "output": "summary.currentSkillScore",
                        "source": "skill_profile.currentSkillScore",
                    },
                    {
                        "output": "summary.learningProgress",
                        "source": "assessments.learning_progress",
                    },
                    {
                        "output": "summary.quizAverage",
                        "source": "assessments.quizAverage",
                    },
                    {
                        "output": "summary.certificationsEarned",
                        "source": "assessments.certifications_earned",
                    },
                    {
                        "output": "charts.skillDistribution",
                        "source": "skill_profile.skillDistribution",
                    },
                    {"output": "charts.skillGaps", "source": "skill_profile.skillGaps"},
                    {
                        "output": "analytics.strongestSkill",
                        "source": "skill_profile.strongestSkill",
                    },
                    {
                        "output": "analytics.weakestSkill",
                        "source": "skill_profile.weakestSkill",
                    },
                    {
                        "output": "analytics.quizPassRate",
                        "source": "assessments.quizAverage",
                    },
                    {"output": "roadmap", "source": "roadmap (passthrough)"},
                ],
                "tolerance": "Failed/timed-out sections produce None/[] defaults; the response shape is always complete.",
            }
        },
    },
    "manager_dashboard": {
        "description": "Manager dashboard computed fields (2-phase build)",
        "phase_1": {
            "source": "SkillProfiler GET /api/v1/me + GET /api/v1/users",
            "fields": [
                {
                    "field": "manager.id",
                    "formula": "userId from /me endpoint",
                    "nullable": False,
                },
                {
                    "field": "manager.name",
                    "formula": "username from /me endpoint",
                    "nullable": True,
                },
                {
                    "field": "manager.department",
                    "formula": "department from /me endpoint",
                    "nullable": True,
                },
            ],
        },
        "phase_2_per_employee": {
            "description": "For each team member, fan out 3 detail calls and produce a member summary",
            "member_summary_fields": [
                {"field": "skillScore", "source": "skill_profile.currentSkillScore"},
                {"field": "learningProgress", "source": "roadmap.completionPercentage"},
                {
                    "field": "skills",
                    "source": "skill_profile.skills (raw dict of skill→score)",
                },
                {"field": "skillGaps", "source": "skill_profile.skillGaps"},
                {"field": "quizAverage", "source": "assessments.quizAverage"},
                {"field": "quizPassRate", "source": "assessments.quizPassRate"},
            ],
        },
        "team_rollups": {
            "description": "Aggregate all member summaries into team-level metrics",
            "fields": [
                {
                    "field": "summary.teamSize",
                    "formula": "len(members) if members else None",
                    "nullable": True,
                },
                {
                    "field": "summary.averageSkillScore",
                    "formula": "round(mean([m.skillScore for m in members]))",
                    "nullable": True,
                },
                {
                    "field": "summary.averageLearningProgress",
                    "formula": "round(mean([m.learningProgress for m in members]))",
                    "nullable": True,
                },
                {
                    "field": "summary.pendingTrainings",
                    "formula": "sum(len(m.skillGaps) for m in members)",
                    "nullable": True,
                },
                {
                    "field": "summary.certificationCompletion",
                    "formula": "round(mean([m.certificationRatio for m in members]) * 100)",
                    "nullable": True,
                },
                {
                    "field": "analytics.topPerformer",
                    "formula": "member name with max skillScore",
                    "nullable": True,
                },
                {
                    "field": "analytics.lowestPerformer",
                    "formula": "member name with min skillScore",
                    "nullable": True,
                },
                {
                    "field": "analytics.trainingCompletionRate",
                    "formula": "round(mean([m.quizAverage for m in members]))",
                    "nullable": True,
                },
                {
                    "field": "analytics.averageQuizScore",
                    "formula": "round(mean([m.quizAverage for m in members]), 1)",
                    "nullable": True,
                },
            ],
            "skill_grouping": {
                "description": "Skills and gaps are categorized into department groups",
                "groups": [
                    {
                        "group": "Backend",
                        "keywords": "python, java, go, rust, c++, c#, kotlin, scala, node.js, typescript, spring, django, fastapi, flask, rest, graphql, sql, postgresql, mysql, mongodb, redis, kafka, ...",
                    },
                    {
                        "group": "Frontend",
                        "keywords": "react, vue, angular, javascript, html, css, next.js, svelte, tailwind, redux, webpack, ...",
                    },
                    {
                        "group": "DevOps",
                        "keywords": "docker, kubernetes, k8s, aws, gcp, azure, terraform, ci/cd, jenkins, helm, ansible, linux, bash, prometheus, grafana, ...",
                    },
                    {
                        "group": "AI",
                        "keywords": "machine learning, deep learning, nlp, tensorflow, pytorch, llm, rag, openai, langchain, generative ai, ...",
                    },
                    {
                        "group": "DataEngineer",
                        "keywords": "spark, hadoop, airflow, etl, data warehouse, bigquery, snowflake, dbt, databricks, pandas, numpy, tableau, power bi, ...",
                    },
                    {
                        "group": "Others",
                        "keywords": "any skill not matching the above groups",
                    },
                ],
                "rule": "For each skill/gap in each member, check if any keyword (case-insensitive substring match) belongs to a group. If no group matches, classify as Others.",
            },
            "distribution_counting": {
                "field": "charts.teamSkillDistribution",
                "formula": "For each skill across all members: group → department category, count unique employees per group, sort by count descending.",
                "example": "Member 1: {python, react, docker}, Member 2: {python, aws}, Member 3: {react} → [{Backend: 2}, {Frontend: 2}, {DevOps: 2}]",
            },
            "gaps_counting": {
                "field": "skillGaps",
                "formula": "For each gap across all members: group gap skill → department category, count employees affected per group, sort by count descending.",
                "example": "Member 1 gap: kubernetes, Member 2 gap: kubernetes, Member 3 gap: react → [{DevOps: 2}, {Frontend: 1}]",
            },
        },
    },
    "executive_dashboard": {
        "description": "Executive dashboard computed fields",
        "parsers": {
            "parse_org_overview": {
                "source": "AI Tutor GET /org/overview",
                "fields": [
                    {
                        "field": "overall_ai_readiness",
                        "formula": "passthrough from upstream (nullable)",
                        "nullable": True,
                    },
                    {
                        "field": "overall_learning_completion",
                        "formula": "passthrough from upstream (nullable)",
                        "nullable": True,
                    },
                    {
                        "field": "training_roi",
                        "formula": "passthrough from upstream (nullable)",
                        "nullable": True,
                    },
                    {
                        "field": "training_cost",
                        "formula": "passthrough from upstream (nullable)",
                        "nullable": True,
                    },
                    {
                        "field": "certification_rate",
                        "formula": "passthrough from upstream (nullable)",
                        "nullable": True,
                    },
                ],
            },
        },
        "assembly": {
            "assemble_executive_dashboard": {
                "description": "Assembles the org-wide executive dashboard from org overview and department rollups",
                "fields": [
                    {
                        "field": "summary.averageSkillScore",
                        "formula": "round(mean([d.avgSkillScore for d in departments if numeric]))",
                        "nullable": True,
                        "example": "department scores: [75, 82, 68] → round(mean([75,82,68])) = 75",
                    },
                    {
                        "field": "analytics.highestPerformingDepartment",
                        "formula": "department name with max avgSkillScore",
                        "nullable": True,
                    },
                    {
                        "field": "analytics.lowestPerformingDepartment",
                        "formula": "department name with min avgSkillScore",
                        "nullable": True,
                    },
                    {
                        "field": "charts.departmentReadiness",
                        "formula": "filter departments where readinessScore is not None → {department, score}",
                        "nullable": False,
                    },
                ],
            }
        },
    },
}


def get_formulas_html() -> str:
    """Render the formulas documentation as a readable HTML string."""
    lines = ["<h1>Dashboard Formulas</h1>"]

    for dashboard_key, dashboard in FORMULAS.items():
        name = dashboard_key.replace("_", " ").title()
        lines.append('<details open style="margin-bottom:1.5em">')
        lines.append(
            f"  <summary><strong>{name}</strong> — {dashboard['description']}</summary>"
        )
        lines.append('  <div style="padding-left:1em">')

        if "parsers" in dashboard:
            for parser_name, parser in dashboard["parsers"].items():
                lines.append('    <details style="margin:1em 0">')
                lines.append(
                    f"      <summary><em>{parser_name}</em> — {parser['source']}</summary>"
                )
                lines.append(
                    '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
                )
                lines.append(
                    "        <tr><th>Field</th><th>Formula</th><th>Nullable</th><th>Example</th></tr>"
                )
                for field in parser["fields"]:
                    formula = field["formula"].replace("\n", "<br>")
                    nullable = str(field.get("nullable", ""))
                    example = field.get("example", "")
                    note = field.get("note", "")
                    if note:
                        note = f"<br><small><em>Note: {note}</em></small>"
                    lines.append(
                        f"        <tr><td><code>{field['field']}</code></td><td>{formula}{note}</td><td>{nullable}</td><td>{example}</td></tr>"
                    )
                lines.append("      </table>")
                lines.append("    </details>")

        if "assembly" in dashboard:
            for asm_name, asm in dashboard["assembly"].items():
                lines.append('    <details style="margin:1em 0">')
                lines.append(
                    f"      <summary><em>{asm_name}</em> — {asm['description']}</summary>"
                )
                if "field_mappings" in asm:
                    lines.append(
                        '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
                    )
                    lines.append(
                        "        <tr><th>Output Field</th><th>Source</th></tr>"
                    )
                    for mapping in asm["field_mappings"]:
                        lines.append(
                            f"        <tr><td><code>{mapping['output']}</code></td><td>{mapping['source']}</td></tr>"
                        )
                    lines.append("      </table>")
                if "tolerance" in asm:
                    lines.append(f"      <p><em>Tolerance: {asm['tolerance']}</em></p>")
                lines.append("    </details>")

        if "phase_1" in dashboard:
            p1 = dashboard["phase_1"]
            lines.append('    <details style="margin:1em 0">')
            lines.append(f"      <summary><em>Phase 1</em> — {p1['source']}</summary>")
            lines.append(
                '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
            )
            lines.append(
                "        <tr><th>Field</th><th>Formula</th><th>Nullable</th></tr>"
            )
            for field in p1["fields"]:
                lines.append(
                    f"        <tr><td><code>{field['field']}</code></td><td>{field['formula']}</td><td>{field['nullable']}</td></tr>"
                )
            lines.append("      </table>")
            lines.append("    </details>")

        if "phase_2_per_employee" in dashboard:
            p2 = dashboard["phase_2_per_employee"]
            lines.append('    <details style="margin:1em 0">')
            lines.append(
                f"      <summary><em>Phase 2 — Per-Employee Details</em> — {p2['description']}</summary>"
            )
            lines.append(
                '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
            )
            lines.append("        <tr><th>Member Field</th><th>Source</th></tr>")
            for field in p2["member_summary_fields"]:
                lines.append(
                    f"        <tr><td><code>{field['field']}</code></td><td>{field['source']}</td></tr>"
                )
            lines.append("      </table>")
            lines.append("    </details>")

        if "team_rollups" in dashboard:
            tr = dashboard["team_rollups"]
            lines.append('    <details style="margin:1em 0">')
            lines.append(
                f"      <summary><em>Team Rollups</em> — {tr['description']}</summary>"
            )
            lines.append(
                '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
            )
            lines.append(
                "        <tr><th>Field</th><th>Formula</th><th>Nullable</th></tr>"
            )
            for field in tr["fields"]:
                formula = field["formula"].replace("\n", "<br>")
                lines.append(
                    f"        <tr><td><code>{field['field']}</code></td><td>{formula}</td><td>{field['nullable']}</td></tr>"
                )
            lines.append("      </table>")

            if "skill_grouping" in tr:
                sg = tr["skill_grouping"]
                lines.append(f"      <p><strong>{sg['description']}</strong></p>")
                lines.append(
                    '      <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">'
                )
                lines.append(
                    "        <tr><th>Group</th><th>Matching Keywords</th></tr>"
                )
                for g in sg["groups"]:
                    lines.append(
                        f"        <tr><td><code>{g['group']}</code></td><td><code>{g['keywords']}</code></td></tr>"
                    )
                lines.append("      </table>")
                lines.append(f"      <p><em>Rule: {sg['rule']}</em></p>")

            if "distribution_counting" in tr:
                dc = tr["distribution_counting"]
                lines.append(f"      <p><strong>{dc['field']}</strong></p>")
                lines.append(f"      <p><em>Formula:</em> {dc['formula']}</p>")
                lines.append(f"      <p><em>Example:</em> {dc['example']}</p>")

            if "gaps_counting" in tr:
                gc = tr["gaps_counting"]
                lines.append(f"      <p><strong>{gc['field']}</strong></p>")
                lines.append(f"      <p><em>Formula:</em> {gc['formula']}</p>")
                lines.append(f"      <p><em>Example:</em> {gc['example']}</p>")

            lines.append("    </details>")

        lines.append("  </div>")
        lines.append("</details>")

    return "\n".join(lines)
