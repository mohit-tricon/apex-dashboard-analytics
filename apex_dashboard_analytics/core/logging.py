"""Structured logging configuration using structlog.

This module wires structlog together with the standard library ``logging``
module so that logs emitted by structlog *and* by third-party libraries
(uvicorn, fastapi, etc.) share a single, consistent format and set of
output handlers (console + rotating file).
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from apex_dashboard_analytics.core.config import get_settings

import structlog

_configured = False
settings = get_settings()

def _build_shared_processors() -> list[structlog.typing.Processor]:
    """Processors applied to *every* log record (structlog and stdlib)."""
    return [
        # Merge request-scoped context bound via structlog.contextvars.
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        # Render stdlib %-style args (uvicorn uses these) into the message.
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]


def _make_formatter(
    renderer: structlog.typing.Processor,
    shared_processors: list[structlog.typing.Processor],
    *,
    json_tracebacks: bool,
) -> structlog.stdlib.ProcessorFormatter:
    """Build a ``ProcessorFormatter`` for a stdlib handler.

    ``foreign_pre_chain`` runs on records coming from stdlib loggers so they
    are enriched exactly like structlog-native records.
    """
    processors: list[structlog.typing.Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
    ]
    if json_tracebacks:
        # Structured, machine-readable tracebacks for the JSON sinks.
        processors.append(structlog.processors.dict_tracebacks)
    processors.append(renderer)

    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=processors,
    )


def configure_logging(
    *,
    log_level: str = "DEBUG",
    json_logs: bool = False,
    log_to_file: bool = True,
    log_file: str = "logs/app.log",
    log_file_max_bytes: int = 10 * 1024 * 1024,
    log_file_backup_count: int = 5,
    force: bool = False,
) -> None:
    """Configure structlog and the stdlib logging bridge.

    Both structlog and standard-library log records flow through a shared
    processor chain and are emitted to stdout and (optionally) a rotating
    JSON log file.

    Args:
        log_level: Minimum log level, e.g. ``"INFO"``.
        json_logs: When ``True`` emit JSON to the console (useful in
            production); otherwise emit human-friendly console logs.
        log_to_file: When ``True`` also write JSON logs to ``log_file``.
        log_file: Path to the log file (parent dirs are created).
        log_file_max_bytes: Max size per file before rotation.
        log_file_backup_count: Number of rotated files to retain.
        force: Reconfigure even if logging was already configured.
    """
    global _configured
    
    if _configured and not force:
        return

    json_logs = True
    if settings.is_production:
        log_level = "INFO"

    level = getattr(logging, log_level.upper(), logging.INFO)
    shared_processors = _build_shared_processors()

    # structlog-native records: enrich, then hand off to ProcessorFormatter.
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handlers: list[logging.Handler] = []

    # Console handler: JSON in prod, pretty ConsoleRenderer in dev.
    console_renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer()
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        _make_formatter(console_renderer, shared_processors, json_tracebacks=json_logs)
    )
    handlers.append(console_handler)

    # Rotating file handler: always JSON for easy parsing/ingestion.
    if log_to_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=path,
            maxBytes=log_file_max_bytes,
            backupCount=log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            _make_formatter(
                structlog.processors.JSONRenderer(),
                shared_processors,
                json_tracebacks=True,
            )
        )
        handlers.append(file_handler)

    # Route everything (structlog + uvicorn/fastapi/etc.) through our handlers.
    root = logging.getLogger()
    root.handlers = handlers
    root.setLevel(level)

    # Let uvicorn/gunicorn loggers propagate to the root instead of using
    # their own handlers, so all output is formatted consistently.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True

    _configured = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name, app_name=settings.app_name, environment=settings.environment)
