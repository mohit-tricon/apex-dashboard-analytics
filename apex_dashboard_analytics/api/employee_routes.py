import time
from fastapi.routing import APIRouter
from fastapi import Request


employee_router = APIRouter(prefix="/employees")


@employee_router.get("/check/")
def check_endpoint(request: Request):
    request.state.logger.info("This is one request logged")
    request.state.logger.info("This is second request logged")
    return {
        "message": "Check endpoint"
    }