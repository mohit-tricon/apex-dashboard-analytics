
from fastapi.routing import APIRouter


employee_router = APIRouter(prefix="/employees")


@employee_router.get("/check/")
def check_endpoint():
    return {
        "message": "Check endpoint"
    }