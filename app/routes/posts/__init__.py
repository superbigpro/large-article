from fastapi import APIRouter
from .get import router as get_router
from .create import router as create_router

router = APIRouter()

router.include_router(get_router)
router.include_router(create_router)