"""
SmartCompile Backend Main Application.

Entry point for the FastAPI server.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.database import init_db
from backend.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smartcompile")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure SQLite database tables exist
    logger.info("Initializing SmartCompile SQLite database...")
    init_db(settings.DATABASE_PATH)
    logger.info(f"SmartCompile initialized with active AI provider: '{settings.active_provider}'")
    yield
    logger.info("SmartCompile backend shutting down.")


app = FastAPI(
    title="SmartCompile API",
    description="Intelligent AI Code Optimization, Compiler Routing & Caching Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "app": "SmartCompile API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "active_provider": settings.active_provider,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
