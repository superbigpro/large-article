from fastapi import APIRouter
from .health_check import router as healthcheck_router

router = APIRouter(prefix="/api")

router.include_router(healthcheck_router)