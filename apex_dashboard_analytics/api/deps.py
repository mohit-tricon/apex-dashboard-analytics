"""FastAPI dependencies shared across route modules."""

from __future__ import annotations

from fastapi import Header, HTTPException, Query

_MOCK_TRUTHY = frozenset({"1", "true", "yes"})


def use_mock_data(
    x_use_mock_data: str | None = Header(
        default=None,
        alias="X-Use-Mock-Data",
        description="When true, return deterministic mock payloads for frontend integration.",
    ),
    use_mock: bool = Query(
        default=False,
        description="Same as X-Use-Mock-Data header; useful when headers are hard to set locally.",
    ),
) -> bool:
    """Resolve whether assessment-backed routes should serve mock_data instead."""
    if use_mock:
        return True
    if x_use_mock_data is None:
        return False
    return x_use_mock_data.strip().lower() in _MOCK_TRUTHY


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
