from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import TransactionCreate
from app.services.fraud_detection import FraudDetectionService


class TransactionService:
    def __init__(self):
        self.fraud_service = FraudDetectionService()

    async def process_transaction(
        self,
        transaction_data: TransactionCreate,
        db: AsyncSession
    ) -> Transaction:
        # Create transaction record
        transaction = Transaction(
            transaction_id=transaction_data.transaction_id,
            card_number=transaction_data.card_number,
            amount=transaction_data.amount,
            currency=transaction_data.currency,
            merchant_id=transaction_data.merchant_id,
            merchant_name=transaction_data.merchant_name,
            merchant_category=transaction_data.merchant_category,
            location_lat=transaction_data.location_lat,
            location_lon=transaction_data.location_lon
        )

        # Analyze for fraud
        fraud_score, features = await self.fraud_service.analyze_transaction(
            transaction_data, db
        )

        # Update transaction with fraud analysis
        transaction.fraud_score = fraud_score
        transaction.features_json = str(features)

        # Determine status based on fraud score
        if fraud_score >= 0.8:
            transaction.status = TransactionStatus.DECLINED
            transaction.is_fraud = True
        elif fraud_score >= 0.6:
            transaction.status = TransactionStatus.FLAGGED
        else:
            transaction.status = TransactionStatus.APPROVED

        db.add(transaction)
        await db.flush()
        await db.refresh(transaction)

        return transaction

    async def get_transaction_by_id(
        self,
        transaction_id: int,
        db: AsyncSession
    ) -> Optional[Transaction]:
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_transaction_by_external_id(
        self,
        external_transaction_id: str,
        db: AsyncSession
    ) -> Optional[Transaction]:
        query = select(Transaction).where(
            Transaction.transaction_id == external_transaction_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
