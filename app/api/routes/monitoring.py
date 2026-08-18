from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any

from app.models.database import get_db
from app.models.transaction import Transaction
from app.models.alert import Alert, AlertStatus
from app.api.websockets import get_websocket_manager, ConnectionManager
from app.utils.redis_client import get_redis, RedisClient

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    ws_manager: ConnectionManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)

    # Transaction metrics
    total_transactions_query = select(func.count(Transaction.id))
    total_transactions_result = await db.execute(total_transactions_query)
    total_transactions = total_transactions_result.scalar()

    # Transactions last hour
    last_hour_query = select(func.count(Transaction.id)).where(
        Transaction.created_at >= one_hour_ago
    )
    last_hour_result = await db.execute(last_hour_query)
    transactions_last_hour = last_hour_result.scalar()

    # Fraud transactions
    fraud_query = select(func.count(Transaction.id)).where(Transaction.is_fraud == True)
    fraud_result = await db.execute(fraud_query)
    total_fraud = fraud_result.scalar()

    # Fraud last hour
    fraud_last_hour_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.created_at >= one_hour_ago,
            Transaction.is_fraud == True
        )
    )
    fraud_last_hour_result = await db.execute(fraud_last_hour_query)
    fraud_last_hour = fraud_last_hour_result.scalar()

    # Average fraud score
    avg_score_query = select(func.avg(Transaction.fraud_score))
    avg_score_result = await db.execute(avg_score_query)
    avg_fraud_score = avg_score_result.scalar() or 0.0

    # Alert metrics
    open_alerts_query = select(func.count(Alert.id)).where(Alert.status == AlertStatus.OPEN)
    open_alerts_result = await db.execute(open_alerts_query)
    open_alerts = open_alerts_result.scalar()

    # Calculate fraud rate
    fraud_rate = total_fraud / total_transactions if total_transactions > 0 else 0.0

    # Transactions per second (approximate)
    transactions_per_second = transactions_last_hour / 3600 if transactions_last_hour else 0

    return {
        "timestamp": now.isoformat(),
        "transactions": {
            "total": total_transactions,
            "last_hour": transactions_last_hour,
            "per_second": round(transactions_per_second, 2)
        },
        "fraud": {
            "total": total_fraud,
            "last_hour": fraud_last_hour,
            "rate": round(fraud_rate, 4),
            "average_score": round(avg_fraud_score, 4)
        },
        "alerts": {
            "open": open_alerts
        },
        "websocket_connections": ws_manager.get_connection_count()
    }


@router.get("/realtime")
async def get_realtime_metrics(
    redis: RedisClient = Depends(get_redis)
) -> Dict[str, Any]:
    # Get real-time metrics from Redis
    now = datetime.utcnow()

    # Simulated real-time metrics (in production, these would come from Redis counters)
    return {
        "timestamp": now.isoformat(),
        "transactions_per_second": 0,
        "current_queue_size": 0,
        "model_latency_ms": 0,
        "active_connections": 0
    }


@router.post("/broadcast-test")
async def broadcast_test_message(
    ws_manager: ConnectionManager = Depends(get_websocket_manager)
):
    test_message = {
        "type": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "This is a test broadcast message"
    }
    await ws_manager.broadcast(test_message)
    return {"status": "Test message broadcasted"}
