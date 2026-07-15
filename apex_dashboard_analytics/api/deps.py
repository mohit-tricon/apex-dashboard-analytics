"""FastAPI dependencies shared across route modules."""

from __future__ import annotations

from fastapi import Header, HTTPException


def get_scoped_employee_id(
    x_employee_id: str | None = Header(default=None, alias="X-Employee-Id"),
) -> str:
    """Resolve the employee context for course-scoped quiz attempt routes.

    The API gateway sets ``X-Employee-Id`` when forwarding manager or
    employee requests (see platform RBAC contract Section 4.4).
    """
    if not x_employee_id:
        raise HTTPException(status_code=401, detail="X-Employee-Id header required")
    return x_employee_id
