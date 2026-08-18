from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any

from app.models.database import get_db
from app.utils.redis_client import get_redis, RedisClient
from app.api.websockets import get_websocket_manager, ConnectionManager

router = APIRouter()


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    ws_manager: ConnectionManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        await redis.redis.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # WebSocket connections
    health_status["services"]["websockets"] = {
        "status": "healthy",
        "active_connections": ws_manager.get_connection_count()
    }

    return health_status


@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    ws_manager: ConnectionManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_websocket_connections": ws_manager.get_connection_count(),
        "redis_connected": await redis.redis.ping()
    }
