import numpy as np
from typing import Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.config import settings
from app.ml.predictor import FraudPredictor
from app.schemas.transaction import TransactionCreate
from app.models.transaction import Transaction


class FraudDetectionService:
    def __init__(self):
        self.predictor = FraudPredictor()

    async def analyze_transaction(
        self,
        transaction: TransactionCreate,
        db: AsyncSession = None
    ) -> Tuple[float, Dict[str, Any]]:
        # Extract features
        features = await self._extract_features(transaction, db)

        # Get prediction
        fraud_score = await self.predictor.predict(features)

        return fraud_score, features

    async def _extract_features(
        self,
        transaction: TransactionCreate,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        features = {}

        # Basic transaction features
        features["amount"] = transaction.amount
        features["amount_log"] = np.log1p(transaction.amount)

        # Time-based features
        now = datetime.utcnow()
        features["hour_of_day"] = now.hour
        features["day_of_week"] = now.weekday()
        features["is_weekend"] = 1 if now.weekday() >= 5 else 0
        features["is_night"] = 1 if now.hour < 6 or now.hour > 22 else 0

        # Merchant category encoding (simplified)
        category_risk = {
            "grocery": 0.1,
            "restaurant": 0.2,
            "gas": 0.3,
            "online": 0.7,
            "jewelry": 0.8,
            "electronics": 0.6,
            "travel": 0.9,
            "entertainment": 0.4
        }
        features["category_risk"] = category_risk.get(
            transaction.merchant_category.lower(),
            0.5  # Default risk
        )

        # Location features (simplified)
        if transaction.location_lat and transaction.location_lon:
            features["has_location"] = 1
            features["location_lat"] = transaction.location_lat
            features["location_lon"] = transaction.location_lon
        else:
            features["has_location"] = 0
            features["location_lat"] = 0
            features["location_lon"] = 0

        # Historical features (if database available)
        if db:
            historical_features = await self._get_historical_features(
                transaction.card_number, db
            )
            features.update(historical_features)
        else:
            # Default values when no historical data
            features["transaction_count_1h"] = 0
            features["transaction_count_24h"] = 0
            features["avg_amount_24h"] = 0
            features["amount_deviation"] = 0
            features["unique_merchants_24h"] = 0

        return features

    async def _get_historical_features(
        self,
        card_number: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        # Transaction count last hour
        count_1h_query = select(func.count(Transaction.id)).where(
            and_(
                Transaction.card_number == card_number,
                Transaction.created_at >= one_hour_ago
            )
        )
        count_1h_result = await db.execute(count_1h_query)
        transaction_count_1h = count_1h_result.scalar()

        # Transaction count last 24 hours
        count_24h_query = select(func.count(Transaction.id)).where(
            and_(
                Transaction.card_number == card_number,
                Transaction.created_at >= one_day_ago
            )
        )
        count_24h_result = await db.execute(count_24h_query)
        transaction_count_24h = count_24h_result.scalar()

        # Average amount last 24 hours
        avg_amount_query = select(func.avg(Transaction.amount)).where(
            and_(
                Transaction.card_number == card_number,
                Transaction.created_at >= one_day_ago
            )
        )
        avg_amount_result = await db.execute(avg_amount_query)
        avg_amount_24h = avg_amount_result.scalar() or 0.0

        # Unique merchants last 24 hours
        unique_merchants_query = select(func.count(func.distinct(Transaction.merchant_id))).where(
            and_(
                Transaction.card_number == card_number,
                Transaction.created_at >= one_day_ago
            )
        )
        unique_merchants_result = await db.execute(unique_merchants_query)
        unique_merchants_24h = unique_merchants_result.scalar()

        return {
            "transaction_count_1h": transaction_count_1h,
            "transaction_count_24h": transaction_count_24h,
            "avg_amount_24h": avg_amount_24h,
            "unique_merchants_24h": unique_merchants_24h
        }


# Import needed for historical features
from sqlalchemy import func, and_
