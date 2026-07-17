"""ORM model for the ``integration_logs`` table.

This table records every outbound integration request/response, regardless of
which team's service is being integrated with.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from apex_dashboard_analytics.core.database import Base


class IntegrationLog(Base):
    """A single outbound integration call log entry."""

    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Which team/service this call targeted (e.g. "skill_profiler").
    integration_name: Mapped[str | None] = mapped_column(String(255), index=True)

    method: Mapped[str | None] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, index=True)

    request_headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    response_headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    payload: Mapped[Any | None] = mapped_column(JSONB)
    # Raw response body stored as text (may be JSON, HTML, plain text, etc.).
    response: Mapped[str | None] = mapped_column(Text)

    duration_ms: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)

    # Correlates the integration call with the inbound request that triggered it.
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<IntegrationLog id={self.id} integration={self.integration_name!r} "
            f"{self.method} {self.url} status={self.status_code}>"
        )
