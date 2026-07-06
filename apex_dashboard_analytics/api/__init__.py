from fastapi.routing import APIRouter

from apex_dashboard_analytics.api.employee_routes import employee_router
from apex_dashboard_analytics.api.manager_routes import manager_router


v1_router = APIRouter()

v1_router.include_router(employee_router)
v1_router.include_router(manager_router)

__all__ = ["v1_router"]
