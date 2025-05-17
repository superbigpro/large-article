from fastapi import APIRouter
from .get import router as get_router
from .create import router as create_router
from .update import router as update_router
from .delete import router as delete_router
from .detail_get import router as detailget_router
from .hearts import router as hearts_router

router = APIRouter()

router.include_router(get_router)
router.include_router(create_router)
router.include_router(update_router)
router.include_router(delete_router)   
router.include_router(detailget_router) 
router.include_router(hearts_router) 