from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import json

from app.config import settings
from app.models.database import engine, Base
from app.utils.redis_client import redis_client
from app.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)
logger = get_logger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Credit Card Fraud Detection API")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Connect to Redis
    await redis_client.connect()
    logger.info("Connected to Redis")

    yield

    # Shutdown
    logger.info("Shutting down Credit Card Fraud Detection API")
    await redis_client.disconnect()
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Credit Card Fraud Detection API",
    description="Real-time monitoring API for credit card fraud detection",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.routes import transactions, alerts, health, monitoring
from app.api.websockets import manager

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])


@app.get("/")
async def root():
    return {
        "message": "Credit Card Fraud Detection API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                # Client can subscribe to specific channels
                channel = message.get("channel", "all")
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
