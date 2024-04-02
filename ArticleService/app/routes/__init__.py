# routes/__init__.py

from fastapi import FastAPI
from .posts import router as posts_router
from .comments import router as comments_router

def include_router(app: FastAPI):
    app.include_router(posts_router)
    app.include_router(comments_router)
