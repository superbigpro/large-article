from fastapi import APIRouter
from .finalsubmit import router as finalsubmit_router
from .get import router as get_router
from .submit import router as submit_router

router = APIRouter()

router.include_router(finalsubmit_router)
router.include_router(get_router)
router.include_router(submit_router)