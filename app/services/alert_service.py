from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.transaction import Transaction
from app.api.websockets import get_websocket_manager
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AlertService:
    async def create_alert_from_transaction(
        self,
        transaction: Transaction,
        db: AsyncSession
    ) -> Optional[Alert]:
        # Determine severity based on fraud score
        severity = self._determine_severity(transaction.fraud_score)

        # Create alert reason
        reason = self._create_alert_reason(transaction)

        # Create alert
        alert = Alert(
            transaction_id=transaction.id,
            severity=severity,
            fraud_score=transaction.fraud_score,
            reason=reason,
            status=AlertStatus.OPEN
        )

        db.add(alert)
        await db.flush()
        await db.refresh(alert)

        # Broadcast alert via WebSocket
        ws_manager = await get_websocket_manager()
        await ws_manager.broadcast_alert({
            "id": alert.id,
            "transaction_id": alert.transaction_id,
            "severity": alert.severity.value,
            "fraud_score": alert.fraud_score,
            "reason": alert.reason,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat()
        })

        logger.info(f"Created alert {alert.id} for transaction {transaction.transaction_id}")

        return alert

    def _determine_severity(self, fraud_score: float) -> AlertSeverity:
        if fraud_score >= 0.9:
            return AlertSeverity.CRITICAL
        elif fraud_score >= 0.8:
            return AlertSeverity.HIGH
        elif fraud_score >= 0.7:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _create_alert_reason(self, transaction: Transaction) -> str:
        reasons = []

        if transaction.fraud_score >= 0.8:
            reasons.append("High fraud score detected")

        if transaction.amount > 1000:
            reasons.append("Large transaction amount")

        if transaction.merchant_category.lower() in ["online", "travel", "jewelry"]:
            reasons.append(f"High-risk merchant category: {transaction.merchant_category}")

        return "; ".join(reasons) if reasons else "Transaction flagged for review"
