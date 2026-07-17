"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi.middleware.cors import CORSMiddleware

from apex_dashboard_analytics.api import health_router, tutor_router, v1_router
from apex_dashboard_analytics.core import get_settings, configure_logging, get_logger
from apex_dashboard_analytics.core.database import db
from apex_dashboard_analytics.middlewares import add_request_logger_middleware
from apex_dashboard_analytics.responses import CustomJSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:

    configure_logging()  # configure before creating any logger

    setattr(
        app.state, "logger", get_logger()
    )  # logger available at app level for configurations
    logger = app.state.logger
    logger.info(f"Starting up the App {app.title}")

    # Initialize the database singleton (engine creation is lazy).
    settings = get_settings()
    db.init(
        dsn=settings.sqlalchemy_dsn,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    # Auto-create tables ONLY outside production. In production the schema is
    # owned by migrations (Alembic), not by the app. create_all() is idempotent
    # (checkfirst=True) so it never recreates existing tables, but running DDL
    # from the app on every boot is undesirable in production.
    if settings.db_auto_create_tables and not settings.is_production:
        try:
            db.create_all()
            logger.info("db_tables_ready")
        except Exception:
            # Don't crash startup if the DB is unreachable; log and continue.
            logger.exception("db_create_all_failed")
    elif settings.is_production:
        logger.info("db_schema_managed_by_migrations")

    yield

    db.dispose()
    logger.info("Shuting down the App")


def create_app() -> FastAPI:
    """Create and configure a FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        default_response_class=CustomJSONResponse,
    )
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    app.include_router(
        tutor_router
    )  # no /api/v1 prefix — matches Team 3's literal /tutor/... paths

    add_request_logger_middleware(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# ASGI app for uvicorn: `uvicorn apex_dashboard_analytics.main:app`
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, port=8000, host="0.0.0.0")
