"""Load mock dashboard payloads from the bundled JSON files.

These files (``employees.json``, ``managers.json``, ``executive.json``) hold
frontend-shaped mock responses used *only* when a request opts into mock mode
(see ``api.deps.use_mock_data``). Files are read once and cached.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def _load(filename: str) -> dict[str, Any]:
    with (_DATA_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


def get_employee_dashboard(employee_id: str) -> dict[str, Any] | None:
    """Return the mock employee dashboard for ``employee_id`` (or None)."""
    return _load("employees.json").get(employee_id)


def get_manager_dashboard(manager_id: str) -> dict[str, Any] | None:
    """Return the mock manager dashboard for ``manager_id`` (or None)."""
    return _load("managers.json").get(manager_id)


def get_executive_dashboard(executive_id: str | None = None) -> dict[str, Any] | None:
    """Return a mock executive dashboard.

    With no ``executive_id`` the sole/first executive record is returned
    (the Executive view endpoint is not id-scoped).
    """
    data = _load("executive.json")
    if executive_id is not None:
        return data.get(executive_id)
    return next(iter(data.values()), None)
