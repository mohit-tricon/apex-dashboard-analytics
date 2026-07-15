from fastapi.routing import APIRouter

health_router = APIRouter()


@health_router.get("/health")
def health_check() -> dict:
    """Service health & metadata."""
    return {
        "status": "ok",
        "service": "apex-dashboard-analytics",
    }