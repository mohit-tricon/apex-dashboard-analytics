"""Abstract base class for all team-wise external integrations.

Every team-specific integration (skill profiler, learning recommendation,
AI tutor, assessment, ...) should subclass :class:`BaseIntegration`.

The base class provides:
    * ``make_request``            - perform an HTTP call (sync httpx.Client),
      time it, emit application logs, and persist an integration-log row.
    * ``save_to_integration_log`` - persist a row to ``integration_logs``.
      This NEVER raises: a logging failure must not break the integration.

Child classes are intentionally NOT implemented here.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Mapping

import httpx
import structlog

from apex_dashboard_analytics.core.database import db
from apex_dashboard_analytics.core.logging import get_logger
from apex_dashboard_analytics.models.integration_log import IntegrationLog

# Header names whose values are redacted before being persisted/logged.
SENSITIVE_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
}
_REDACTED = "***REDACTED***"


class BaseIntegration(ABC):
    """Base class encapsulating outbound HTTP integration + logging."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = dict(default_headers or {})
        # Application logger (distinct from the DB integration log).
        self.application_logger = get_logger(f"integration.{self.integration_name}")

    # ------------------------------------------------------------------ #
    # Subclass contract
    # ------------------------------------------------------------------ #
    @property
    @abstractmethod
    def integration_name(self) -> str:
        """Short, stable name of the integrated team/service.

        Subclasses must define this (e.g. ``"skill_profiler"``); it is stored
        on every ``integration_logs`` row.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # HTTP
    # ------------------------------------------------------------------ #
    def make_request(
        self,
        method: str,
        path: str = "",
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Perform an HTTP request and record it in ``integration_logs``.

        Application-level events are emitted via ``application_logger``; the
        request/response is always persisted (success or failure) via
        :meth:`save_to_integration_log`. The underlying HTTP error, if any, is
        re-raised to the caller after the log row has been written.
        """
        url = self._build_url(path)
        request_headers = dict(self.default_headers)
        if headers:
            request_headers.update(headers)
        request_id = self._current_request_id()
        payload = json if json is not None else data

        started = time.perf_counter()
        response: httpx.Response | None = None
        status_code: int | None = None
        response_headers: dict[str, str] | None = None
        response_body: str | None = None
        error: str | None = None

        self.application_logger.info(
            "integration_request_started", method=method, url=url
        )
        try:
            with httpx.Client(timeout=timeout or self.timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers=request_headers,
                    params=params,
                    json=json,
                    data=data,
                )
            assert response is not None
            status_code = response.status_code
            response_headers = dict(response.headers)
            response_body = response.text
            self.application_logger.info(
                "integration_request_finished",
                method=method,
                url=url,
                status_code=status_code,
                duration_ms=self._elapsed_ms(started),
            )
            return response
        except Exception as exc:
            error = repr(exc)
            self.application_logger.exception(
                "integration_request_failed", method=method, url=url
            )
            raise
        finally:
            self.save_to_integration_log(
                url=url,
                method=method,
                request_headers=self._redact(request_headers),
                response_headers=self._redact(response_headers),
                payload=payload,
                response=response_body,
                status_code=status_code,
                duration_ms=self._elapsed_ms(started),
                error=error,
                request_id=request_id,
            )

    # ------------------------------------------------------------------ #
    # Persistence (must never raise)
    # ------------------------------------------------------------------ #
    def save_to_integration_log(
        self,
        *,
        url: str,
        method: str | None = None,
        request_headers: dict[str, Any] | None = None,
        response_headers: dict[str, Any] | None = None,
        payload: Any | None = None,
        response: str | None = None,
        status_code: int | None = None,
        duration_ms: float | None = None,
        error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Persist one integration-log row.

        Deliberately swallows all exceptions: failing to write a log row must
        never break the actual integration flow. Failures are reported through
        the application logger instead.
        """
        try:
            with db.session() as session:
                session.add(
                    IntegrationLog(
                        integration_name=self.integration_name,
                        url=url,
                        method=method,
                        request_headers=request_headers,
                        response_headers=response_headers,
                        payload=payload,
                        response=response,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        error=error,
                        request_id=request_id,
                    )
                )
        except Exception:
            # Never propagate - just record that logging failed.
            self.application_logger.exception(
                "failed_to_save_integration_log", url=url, status_code=status_code
            )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _build_url(self, path: str) -> str:
        if not path:
            return self.base_url
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 2)

    @staticmethod
    def _current_request_id() -> str | None:
        """Pull the inbound request id bound by the logging middleware."""
        return structlog.contextvars.get_contextvars().get("request_id")

    @staticmethod
    def _redact(headers: Mapping[str, str] | None) -> dict[str, str] | None:
        if not headers:
            return None
        return {
            key: (_REDACTED if key.lower() in SENSITIVE_HEADERS else value)
            for key, value in headers.items()
        }
