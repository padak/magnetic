"""Main FastAPI application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from datetime import timedelta

from ..config.settings import Config
from ..config.logging import setup_logging
from magnetic.database import get_db, init_db
from magnetic.services.cache import cache
from magnetic.utils.decorators import cached
from .routes import trips

# Set up logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Magnetic API",
    description="API for the Magnetic travel planning application",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trips.router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await cache.connect()
    init_db()  # Initialize database tables

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    await cache.disconnect()

@app.get("/")
@cached(expire=timedelta(minutes=5))
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": Config.environment
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    services = {
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Test database connection
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
            services["database"] = "healthy"
    except Exception as e:
        services["database"] = f"error: {str(e)}"
    
    # Test Redis connection
    try:
        if await cache.exists("health_check"):
            services["redis"] = "healthy"
        else:
            await cache.set("health_check", "ok", expire=60)
            services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    status = "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy"
    
    return {
        "status": status,
        "services": services
    } 