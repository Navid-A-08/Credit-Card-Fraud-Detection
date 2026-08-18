import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import json


class FeatureEngineer:
    def __init__(self):
        self.feature_names = [
            'amount',
            'amount_log',
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_night',
            'category_risk',
            'has_location',
            'transaction_count_1h',
            'transaction_count_24h',
            'avg_amount_24h',
            'unique_merchants_24h'
        ]

    def extract_features(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        features = []

        # Amount features
        amount = transaction_data.get('amount', 0)
        features.append(amount)
        features.append(np.log1p(amount))

        # Time features
        now = datetime.utcnow()
        features.append(now.hour)
        features.append(now.weekday())
        features.append(1 if now.weekday() >= 5 else 0)
        features.append(1 if now.hour < 6 or now.hour > 22 else 0)

        # Merchant category risk
        category_risk = self._get_category_risk(
            transaction_data.get('merchant_category', '')
        )
        features.append(category_risk)

        # Location features
        has_location = 1 if transaction_data.get('location_lat') else 0
        features.append(has_location)

        # Historical features
        features.append(transaction_data.get('transaction_count_1h', 0))
        features.append(transaction_data.get('transaction_count_24h', 0))
        features.append(transaction_data.get('avg_amount_24h', 0))
        features.append(transaction_data.get('unique_merchants_24h', 0))

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _get_category_risk(self, category: str) -> float:
        category_risk_map = {
            'grocery': 0.1,
            'supermarket': 0.1,
            'restaurant': 0.2,
            'cafe': 0.2,
            'gas': 0.3,
            'fuel': 0.3,
            'online': 0.7,
            'e-commerce': 0.7,
            'jewelry': 0.8,
            'luxury': 0.8,
            'electronics': 0.6,
            'travel': 0.9,
            'airline': 0.9,
            'hotel': 0.85,
            'entertainment': 0.4,
            'gambling': 0.95,
            'cryptocurrency': 0.9
        }

        return category_risk_map.get(category.lower(), 0.5)

    def create_training_features(self, df: pd.DataFrame) -> np.ndarray:
        features = pd.DataFrame()

        # Amount features
        features['amount'] = df['amount']
        features['amount_log'] = np.log1p(df['amount'])
        features['amount_squared'] = df['amount'] ** 2

        # Time features
        if 'created_at' in df.columns:
            features['hour_of_day'] = pd.to_datetime(df['created_at']).dt.hour
            features['day_of_week'] = pd.to_datetime(df['created_at']).dt.dayofweek
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
            features['is_night'] = (
                (features['hour_of_day'] < 6) |
                (features['hour_of_day'] > 22)
            ).astype(int)
        else:
            features['hour_of_day'] = 12
            features['day_of_week'] = 0
            features['is_weekend'] = 0
            features['is_night'] = 0

        # Merchant category risk
        if 'merchant_category' in df.columns:
            features['category_risk'] = df['merchant_category'].apply(
                self._get_category_risk
            )
        else:
            features['category_risk'] = 0.5

        # Location features
        features['has_location'] = (
            df.get('location_lat', pd.Series([0])) != 0
        ).astype(int)

        # Historical features (if available)
        for col in ['transaction_count_1h', 'transaction_count_24h',
                    'avg_amount_24h', 'unique_merchants_24h']:
            if col in df.columns:
                features[col] = df[col]
            else:
                features[col] = 0

        return features.values.astype(np.float32)
