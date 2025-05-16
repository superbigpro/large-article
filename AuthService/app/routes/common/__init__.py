from fastapi import APIRouter
from .health_check import router as healthcheck_router

router = APIRouter()

router.include_router(healthcheck_router)