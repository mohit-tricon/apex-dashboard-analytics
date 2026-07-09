from fastapi.routing import APIRouter

from apex_dashboard_analytics.api.employee_routes import employee_router
from apex_dashboard_analytics.api.executive_routes import executive_router
from apex_dashboard_analytics.api.health_routes import health_router
from apex_dashboard_analytics.api.manager_routes import manager_router
from apex_dashboard_analytics.api.quiz_routes import quiz_router
from apex_dashboard_analytics.api.tutor_routes import tutor_router

# Versioned router — everything that mirrors or aggregates the
# inter-team contracts lives under /api/v1, matching the base URL
# every team's contract doc assumes.
v1_router = APIRouter()

v1_router.include_router(employee_router)
v1_router.include_router(manager_router)
v1_router.include_router(executive_router)
v1_router.include_router(quiz_router)
v1_router.include_router(tutor_router)

__all__ = ["v1_router", "health_router"]