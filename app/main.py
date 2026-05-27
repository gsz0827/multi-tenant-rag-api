from fastapi import FastAPI

from app.api import auth, documents, knowledge_bases, organizations, users
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "AI Knowledge Base API is running",
        "env": settings.APP_ENV,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "env": settings.APP_ENV,
    }


app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(organizations.router, prefix=settings.API_PREFIX)
app.include_router(knowledge_bases.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)