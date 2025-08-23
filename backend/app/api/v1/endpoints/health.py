from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import psutil
import redis.asyncio as redis
from typing import Dict, Any

from ....core.database import get_db
from ....core.config import settings
from ....schemas.common import HealthCheck

router = APIRouter()

# Redis client
redis_client = None


async def get_redis_client():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    return redis_client


@router.get("/", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    start_time = time.time()
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    redis_status = "unknown"
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Calculate uptime
    uptime = time.time() - start_time
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        timestamp=time.time(),
        version=settings.VERSION,
        uptime=uptime,
        database=db_status,
        redis=redis_status
    )


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check with system metrics"""
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "checks": {}
    }
    
    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_data["checks"]["database"] = {"status": "healthy", "response_time": 0}
    except Exception as e:
        health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_data["status"] = "degraded"
    
    # Redis check
    try:
        redis_client = await get_redis_client()
        start_time = time.time()
        await redis_client.ping()
        response_time = time.time() - start_time
        health_data["checks"]["redis"] = {"status": "healthy", "response_time": response_time}
    except Exception as e:
        health_data["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_data["status"] = "degraded"
    
    # System metrics
    health_data["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health_data
