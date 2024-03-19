from fastapi import FastAPI
from .application import router as application_router
from .user import router as user_router


def include_router(app: FastAPI):
    app.include_router(application_router)
    app.include_router(user_router)