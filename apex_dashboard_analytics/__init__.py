"""apex-dashboard-analytics: a FastAPI analytics service."""

from __future__ import annotations


def main() -> None:
    """Run the development server via uvicorn."""
    import uvicorn

    from apex_dashboard_analytics.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "apex_dashboard_analytics.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
