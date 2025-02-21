"""FastAPI application entry point."""

from fastapi import FastAPI
from sqlalchemy import text
import redis.asyncio as redis
from datetime import timedelta

from magnetic.config.settings import config
from magnetic.database import get_db
from magnetic.services.cache import cache
from magnetic.utils.decorators import cached

app = FastAPI(
    title="Magnetic API",
    description="US Family Trip Planner API",
    version="0.1.0",
    debug=config.debug
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await cache.connect()

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
        "environment": config.environment
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