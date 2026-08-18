#!/usr/bin/env python
"""
Training script for fraud detection model.
This script generates synthetic training data and trains the model.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

from app.ml.model import FraudDetectionModel
from app.ml.features import FeatureEngineer
from app.config import settings


def generate_synthetic_data(n_samples: int = 10000) -> tuple:
    """Generate synthetic transaction data for training."""
    print(f"Generating {n_samples} synthetic transactions...")

    data = []
    labels = []

    for _ in range(n_samples):
        # Generate random transaction
        is_fraud = random.random() < 0.1  # 10% fraud rate

        if is_fraud:
            # Fraudulent transactions tend to have certain characteristics
            amount = random.choice([
                random.uniform(1000, 10000),  # Large amounts
                random.uniform(0.01, 1),  # Very small amounts (testing)
            ])
            merchant_category = random.choice(['online', 'travel', 'jewelry', 'electronics'])
            hour = random.choice([0, 1, 2, 3, 4, 23])  # Night hours
            transaction_count_1h = random.randint(5, 20)  # High velocity
        else:
            # Normal transactions
            amount = random.uniform(5, 500)
            merchant_category = random.choice([
                'grocery', 'restaurant', 'gas', 'entertainment', 'retail'
            ])
            hour = random.randint(6, 22)  # Day hours
            transaction_count_1h = random.randint(0, 3)

        transaction = {
            'amount': amount,
            'merchant_category': merchant_category,
            'hour_of_day': hour,
            'day_of_week': random.randint(0, 6),
            'is_weekend': 1 if random.randint(0, 6) >= 5 else 0,
            'is_night': 1 if hour < 6 or hour > 22 else 0,
            'category_risk': FeatureEngineer()._get_category_risk(merchant_category),
            'has_location': random.choice([0, 1]),
            'transaction_count_1h': transaction_count_1h,
            'transaction_count_24h': random.randint(transaction_count_1h, 50),
            'avg_amount_24h': random.uniform(20, 200),
            'unique_merchants_24h': random.randint(1, 10)
        }

        data.append(transaction)
        labels.append(1 if is_fraud else 0)

    return pd.DataFrame(data), np.array(labels)


def train_model():
    """Train the fraud detection model."""
    print("Starting model training...")

    # Generate synthetic data
    df, labels = generate_synthetic_data(n_samples=10000)

    # Create feature engineer
    feature_engineer = FeatureEngineer()

    # Extract features
    print("Extracting features...")
    X = feature_engineer.create_training_features(df)

    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = labels[:split_idx], labels[split_idx:]

    print(f"Training set: {len(X_train)} samples")
    print(f"Validation set: {len(X_val)} samples")
    print(f"Fraud rate: {labels.mean():.2%}")

    # Create and train model
    print("\nCreating model...")
    model = FraudDetectionModel(input_dim=X.shape[1])
    model.summary()

    print("\nTraining model...")
    history = model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=20,
        batch_size=32
    )

    # Save model
    os.makedirs(os.path.dirname(settings.ML_MODEL_PATH), exist_ok=True)
    model.save_model(settings.ML_MODEL_PATH)
    print(f"\nModel saved to {settings.ML_MODEL_PATH}")

    # Evaluate model
    print("\nEvaluating model...")
    val_predictions = model.predict(X_val)
    val_pred_labels = (val_predictions > 0.5).astype(int).flatten()

    accuracy = (val_pred_labels == y_val).mean()
    true_positives = ((val_pred_labels == 1) & (y_val == 1)).sum()
    false_positives = ((val_pred_labels == 1) & (y_val == 0)).sum()
    false_negatives = ((val_pred_labels == 0) & (y_val == 1)).sum()

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"Validation Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1_score:.4f}")

    return history


if __name__ == "__main__":
    train_model()
