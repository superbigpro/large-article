from fastapi import FastAPI
from .posts import router as posts_router
from .user import router as user_router


def include_router(app: FastAPI):
    app.include_router(posts_router)
    app.include_router(user_router)