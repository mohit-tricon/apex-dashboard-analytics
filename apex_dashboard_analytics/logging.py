"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(*, log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog and the stdlib logging bridge.

    Args:
        log_level: Minimum log level, e.g. ``"INFO"``.
        json_logs: When ``True`` emit JSON logs (useful in production),
            otherwise emit human-friendly console logs.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_logs:
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, etc.) through the same configuration.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
