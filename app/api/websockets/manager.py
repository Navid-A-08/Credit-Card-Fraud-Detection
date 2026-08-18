from fastapi import WebSocket
from typing import List, Dict, Set
import json
import asyncio
from datetime import datetime
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_details: Dict[WebSocket, Dict] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        async with self._lock:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.connection_details[websocket] = {
                "connected_at": datetime.utcnow(),
                "client_info": {}
            }
            logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_details:
                del self.connection_details[websocket]
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_transaction(self, transaction_data: dict):
        message = {
            "type": "transaction",
            "timestamp": datetime.utcnow().isoformat(),
            "data": transaction_data
        }
        await self.broadcast(message)

    async def broadcast_alert(self, alert_data: dict):
        message = {
            "type": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        await self.broadcast(message)

    async def broadcast_metrics(self, metrics_data: dict):
        message = {
            "type": "metrics",
            "timestamp": datetime.utcnow().isoformat(),
            "data": metrics_data
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict]:
        return [
            {
                "connected_at": details["connected_at"].isoformat(),
                "client_info": details["client_info"]
            }
            for details in self.connection_details.values()
        ]


# Singleton instance
websocket_manager = ConnectionManager()


async def get_websocket_manager() -> ConnectionManager:
    return websocket_manager
