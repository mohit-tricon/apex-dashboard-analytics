"""Shared constant values used across schemas.

Keeping status/enum-like string values here (SCREAMING_SNAKE_CASE)
avoids "magic strings" scattered across schema files, and gives every
module one place to import them from instead of redefining Literal
values inline.
"""

# Quiz / assessment status values (Team 4 contract: quiz.py)
PASSED = "passed"
FAILED = "failed"
IN_PROGRESS = "in_progress"
NOT_STARTED = "not_started"