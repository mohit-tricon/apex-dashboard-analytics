"""Request logging middleware.

Registers an HTTP middleware that binds a per-request context (request id,
method, path) via ``structlog.contextvars`` so every log line emitted while
handling the request is correlated, and logs the request lifecycle.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "x-request-id"


def add_request_logger_middleware(app: FastAPI) -> None:
    """Attach the request-logging middleware to ``app``.

    Call this from ``create_app`` (before the app starts serving) so the
    middleware is registered on the stack without relying on import
    side-effects or importing ``app`` back into this module.
    """

    @app.middleware("http")
    async def request_logger_middleware(request: Request, call_next) -> Response:
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        start = time.perf_counter()
        start_time = datetime.now(timezone.utc)

        # Bind request_id + start_time so EVERY log line emitted during this
        # request (middleware and route handlers) carries them automatically.
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            start_time=start_time.isoformat(),
        )

        # Expose the request-scoped logger to downstream route handlers.
        # Any call on it inherits the contextvars bound above.
        log = request.app.state.logger
        request.state.logger = log

        log.info("request_started")
        try:
            response = await call_next(request)
        except Exception:
            end_time = datetime.now(timezone.utc)
            log.exception(
                "request_failed",
                end_time=end_time.isoformat(),
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            raise

        # end_time only exists once the request completes, so it is added on
        # the terminal log line (earlier lines cannot know it yet).
        end_time = datetime.now(timezone.utc)
        log.info(
            "request_finished",
            status_code=response.status_code,
            end_time=end_time.isoformat(),
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
