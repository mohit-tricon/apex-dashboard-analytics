"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI


from apex_dashboard_analytics.api import health_router, v1_router
from apex_dashboard_analytics.config import Settings, get_settings
from apex_dashboard_analytics.logging import configure_logging, get_logger
from apex_dashboard_analytics.responses import CustomJSONResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    settings = settings or get_settings()
    configure_logging(log_level=settings.log_level, json_logs=settings.log_json)
    log = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("startup", app_name=settings.app_name, environment=settings.environment)
        yield
        log.info("shutdown", app_name=settings.app_name)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        default_response_class=CustomJSONResponse
    )
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    return app


# ASGI app for uvicorn: `uvicorn apex_dashboard_analytics.main:app`
app = create_app()