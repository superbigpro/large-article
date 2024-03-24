from fastapi import FastAPI
from .user import router as user_router


def include_router(app: FastAPI):
    app.include_router(user_router)