from fastapi import APIRouter
from .login import router as login_router
from .register import router as register_router

router = APIRouter()

router.include_router(login_router)
router.include_router(register_router)