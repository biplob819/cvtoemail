"""FastAPI application entry point."""

import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
# Import all models so create_all sees them
import app.models  # noqa: F401
from app.routers import cv as cv_router
from app.routers import sources as sources_router
from app.routers import jobs as jobs_router
from app.routers import settings as settings_router
from app.routers import dashboard as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (development convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Global exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"\n{'='*60}\nUNHANDLED EXCEPTION on {request.method} {request.url}\n{tb}\n{'='*60}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb},
    )

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(cv_router.router)
app.include_router(sources_router.router)
app.include_router(jobs_router.router)
app.include_router(settings_router.router)
app.include_router(dashboard_router.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
