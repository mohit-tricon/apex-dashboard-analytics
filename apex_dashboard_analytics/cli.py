"""Command-line interface for apex-dashboard-analytics.

Provides the ``apex-dashboard-analytics`` console script with two groups of
commands:

* ``serve``  - run the ASGI app with uvicorn.
* ``db ...`` - a thin stdlib (argparse) wrapper around Alembic so migrations can
  be driven through the app's own entrypoint (no dependency on the ``alembic``
  binary being on PATH). Examples::

      apex-dashboard-analytics db upgrade
      apex-dashboard-analytics db downgrade -1
      apex-dashboard-analytics db revision -m "add column" --autogenerate
      apex-dashboard-analytics db current
      apex-dashboard-analytics db history
      apex-dashboard-analytics db heads
      apex-dashboard-analytics db stamp head
"""

from __future__ import annotations

import argparse
from pathlib import Path

# Project root = parent of the package directory (holds alembic.ini + migrations).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"


def _alembic_config():
    """Build an Alembic ``Config`` with absolute paths (cwd-independent)."""
    from alembic.config import Config

    cfg = Config(str(ALEMBIC_INI))
    # Resolve script_location absolutely so it works from any cwd.
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return cfg


# --------------------------------------------------------------------------- #
# serve
# --------------------------------------------------------------------------- #
def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from apex_dashboard_analytics.core import get_settings

    settings = get_settings()
    uvicorn.run(
        "apex_dashboard_analytics.main:app",
        host=args.host or settings.host,
        port=args.port or settings.port,
        reload=args.reload or settings.debug,
        log_level=settings.log_level.lower(),
    )
    return 0


# --------------------------------------------------------------------------- #
# db (Alembic wrapper)
# --------------------------------------------------------------------------- #
def _cmd_db(args: argparse.Namespace) -> int:
    from alembic import command

    cfg = _alembic_config()

    match args.db_command:
        case "upgrade":
            command.upgrade(cfg, args.revision, sql=args.sql)
        case "downgrade":
            command.downgrade(cfg, args.revision, sql=args.sql)
        case "revision":
            command.revision(cfg, message=args.message, autogenerate=args.autogenerate)
        case "current":
            command.current(cfg, verbose=args.verbose)
        case "history":
            command.history(cfg, verbose=args.verbose)
        case "heads":
            command.heads(cfg, verbose=args.verbose)
        case "stamp":
            command.stamp(cfg, args.revision)
        case _:  # pragma: no cover - argparse enforces choices
            raise SystemExit(f"Unknown db command: {args.db_command!r}")
    return 0


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apex-dashboard-analytics")
    sub = parser.add_subparsers(dest="command")

    # serve
    serve = sub.add_parser("serve", help="Run the ASGI app with uvicorn.")
    serve.add_argument("--host", default=None, help="Bind host (default: settings).")
    serve.add_argument(
        "--port", type=int, default=None, help="Bind port (default: settings)."
    )
    serve.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (dev)."
    )
    serve.set_defaults(func=_cmd_serve)

    # db
    db = sub.add_parser("db", help="Database migration commands (Alembic).")
    db_sub = db.add_subparsers(dest="db_command", required=True)

    up = db_sub.add_parser("upgrade", help="Upgrade to a revision (default: head).")
    up.add_argument("revision", nargs="?", default="head")
    up.add_argument(
        "--sql",
        action="store_true",
        help="Emit SQL to stdout instead of running it (offline mode).",
    )
    up.set_defaults(func=_cmd_db)

    down = db_sub.add_parser("downgrade", help="Downgrade to a revision (default: -1).")
    down.add_argument("revision", nargs="?", default="-1")
    down.add_argument(
        "--sql",
        action="store_true",
        help="Emit SQL to stdout instead of running it (offline mode).",
    )
    down.set_defaults(func=_cmd_db)

    rev = db_sub.add_parser("revision", help="Create a new migration.")
    rev.add_argument("-m", "--message", required=True, help="Migration message.")
    rev.add_argument(
        "--autogenerate",
        action="store_true",
        help="Autogenerate from model changes (requires a reachable DB).",
    )
    rev.set_defaults(func=_cmd_db)

    for name, help_text in (
        ("current", "Show the current revision."),
        ("history", "Show the migration history."),
        ("heads", "Show the available heads."),
    ):
        p = db_sub.add_parser(name, help=help_text)
        p.add_argument("-v", "--verbose", action="store_true")
        p.set_defaults(func=_cmd_db)

    stamp = db_sub.add_parser(
        "stamp", help="Set the revision in the DB without running migrations."
    )
    stamp.add_argument("revision", nargs="?", default="head")
    stamp.set_defaults(func=_cmd_db)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for the ``apex-dashboard-analytics`` console script."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Default to `serve` when no subcommand is given (backwards compatible).
    if args.command is None:
        args = parser.parse_args(["serve"])

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
