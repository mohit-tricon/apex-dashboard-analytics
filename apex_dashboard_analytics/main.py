"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from apex_dashboard_analytics.api import v1_router
from apex_dashboard_analytics.core import get_settings, configure_logging, get_logger
from apex_dashboard_analytics.middlewares import add_request_logger_middleware
from apex_dashboard_analytics.responses import CustomJSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:

    configure_logging()                     # configure before creating any logger

    setattr(app.state, 'logger', get_logger())    # logger available at app level for configurations
    app.state.logger.info(f"Starting up the App {app.title}")

    yield
    app.state.logger.info("Shuting down the App")


def create_app() -> FastAPI:
    """Create and configure a FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        default_response_class=CustomJSONResponse
    )

    add_request_logger_middleware(app)
    app.include_router(v1_router)
    return app


# ASGI app for uvicorn: `uvicorn apex_dashboard_analytics.main:app`
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app=app,
        port=8000
    )
