"""Shared constant values used across schemas.

Keeping status/enum-like string values here (SCREAMING_SNAKE_CASE)
avoids "magic strings" scattered across schema files, and gives every
module one place to import them from instead of redefining Literal
values inline.
"""

# Quiz / assessment status values (frontend contract: quiz.py)
PASSED = "passed"
FAILED = "failed"
IN_PROGRESS = "in_progress"
NOT_STARTED = "not_started"

# Assessment service upstream status values
PASS = "pass"
FAIL = "fail"
PENDING = "pending"