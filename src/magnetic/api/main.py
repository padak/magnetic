"""FastAPI application entry point."""

from fastapi import FastAPI
from sqlalchemy import text
import redis.asyncio as redis
from magnetic.config.settings import config
from magnetic.database import get_db

app = FastAPI(
    title="Magnetic API",
    description="US Family Trip Planner API",
    version="0.1.0",
    debug=config.debug
)

@app.get("/")
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
        redis_client = redis.from_url(config.storage_settings["redis_url"])
        await redis_client.ping()
        services["redis"] = "healthy"
        await redis_client.close()
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    status = "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy"
    
    return {
        "status": status,
        "services": services
    } 