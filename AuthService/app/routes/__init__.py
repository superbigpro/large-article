from fastapi import FastAPI
from .user import router as user_router
from .common import router as common_router

def include_router(app: FastAPI):
    app.include_router(user_router)
    app.include_router(common_router)