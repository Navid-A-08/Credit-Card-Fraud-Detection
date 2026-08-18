#!/usr/bin/env python
"""
Standalone test script that verifies the application components work correctly.
Tests ML model, API structure, and feature engineering without requiring database.
"""

import sys
import os
sys.path.append(0)

import numpy as np
from datetime import datetime
import json

def test_feature_engineering():
    """Test the feature engineering pipeline."""
    print("[TEST] Testing Feature Engineering...")

    from app.ml.features import FeatureEngineer

    feature_engineer = FeatureEngineer()

    # Test transaction
    transaction = {
        "amount": 150.00,
        "merchant_category": "online",
        "location_lat": 40.7128,
        "location_lon": -74.0060,
        "transaction_count_1h": 2,
        "transaction_count_24h": 10,
        "avg_amount_24h": 75.50,
        "unique_merchants_24h": 5
    }

    features = feature_engineer.extract_features(transaction)

    assert features.shape == (1, 12), f"Expected shape (1, 12), got {features.shape}"
    assert features[0][0] == 150.0, "Amount mismatch"
    assert features[0][6] > 0, "Category risk should be positive"

    print(f"   [OK] Features extracted: {features.shape}")
    print(f"   [OK] Amount: {features[0][0]}")
    print(f"   [OK] Category risk: {features[0][6]:.2f}")

    return True


def test_ml_model():
    """Test the ML model creation and prediction."""
    print("\n[OK] Testing ML Model...")

    from app.ml.model import FraudDetectionModel

    # Create model
    model = FraudDetectionModel(input_dim=12)
    print("   [OK] Model created successfully")

    # Test prediction with random data
    test_input = np.random.rand(1, 12).astype(np.float32)
    prediction = model.predict(test_input)

    assert prediction.shape == (1, 1), f"Expected shape (1, 1), got {prediction.shape}"
    assert 0 <= prediction[0][0] <= 1, f"Prediction should be between 0 and 1, got {prediction[0][0]}"

    print(f"   [OK] Prediction shape: {prediction.shape}")
    print(f"   [OK] Prediction value: {prediction[0][0]:.4f}")

    return True


def test_fraud_predictor():
    """Test the fraud predictor with rule-based fallback."""
    print("\n[OK] Testing Fraud Predictor...")

    from app.ml.predictor import FraudPredictor

    predictor = FraudPredictor()

    # Test normal transaction
    normal_features = {
        "amount": 50.0,
        "merchant_category": "grocery",
        "has_location": 1,
        "transaction_count_1h": 1,
        "avg_amount_24h": 45.0,
        "category_risk": 0.1
    }

    score_normal = predictor._rule_based_scoring(normal_features)

    # Test suspicious transaction
    suspicious_features = {
        "amount": 2500.0,
        "merchant_category": "online",
        "has_location": 0,
        "transaction_count_1h": 8,
        "avg_amount_24h": 50.0,
        "category_risk": 0.7
    }

    score_suspicious = predictor._rule_based_scoring(suspicious_features)

    assert 0 <= score_normal <= 1, f"Normal score out of range: {score_normal}"
    assert 0 <= score_suspicious <= 1, f"Suspicious score out of range: {score_suspicious}"
    assert score_suspicious > score_normal, "Suspicious should score higher than normal"

    print(f"   [OK] Normal transaction score: {score_normal:.4f}")
    print(f"   [OK] Suspicious transaction score: {score_suspicious:.4f}")
    print(f"   [OK] Detection working: Suspicious > Normal = {score_suspicious > score_normal}")

    return True


def test_api_schemas():
    """Test Pydantic schemas."""
    print("\n[OK] Testing API Schemas...")

    from app.schemas.transaction import TransactionCreate, TransactionResponse
    from app.schemas.alert import AlertCreate, AlertSeverity

    # Test transaction schema
    transaction_data = {
        "transaction_id": "TXN123456",
        "card_number": "4111111111111111",
        "amount": 150.00,
        "merchant_id": "M001",
        "merchant_name": "Amazon",
        "merchant_category": "online"
    }

    transaction = TransactionCreate(**transaction_data)
    assert transaction.transaction_id == "TXN123456"
    assert transaction.amount == 150.00

    print(f"   [OK] TransactionCreate schema validated")

    # Test alert schema
    alert_data = {
        "transaction_id": 1,
        "fraud_score": 0.85,
        "reason": "High fraud score detected",
        "severity": AlertSeverity.HIGH
    }

    alert = AlertCreate(**alert_data)
    assert alert.fraud_score == 0.85
    assert alert.severity == AlertSeverity.HIGH

    print(f"   [OK] AlertCreate schema validated")

    return True


def test_websocket_manager():
    """Test WebSocket manager initialization."""
    print("\n[OK] Testing WebSocket Manager...")

    from app.api.websockets.manager import ConnectionManager

    manager = ConnectionManager()

    assert manager.active_connections == []
    assert manager.connection_details == {}
    assert manager.get_connection_count() == 0

    print(f"   [OK] ConnectionManager initialized")
    print(f"   [OK] Initial connection count: {manager.get_connection_count()}")

    return True


def test_config():
    """Test configuration loading."""
    print("\n[OK] Testing Configuration...")

    from app.config import settings

    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
    assert 0 < settings.FRAUD_THRESHOLD <= 1
    assert settings.JWT_SECRET_KEY is not None

    print(f"   [OK] DATABASE_URL: {settings.DATABASE_URL[:30]}...")
    print(f"   [OK] REDIS_URL: {settings.REDIS_URL}")
    print(f"   [OK] FRAUD_THRESHOLD: {settings.FRAUD_THRESHOLD}")

    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Credit Card Fraud Detection API - Component Tests")
    print("=" * 60)

    tests = [
        test_feature_engineering,
        test_ml_model,
        test_fraud_predictor,
        test_api_schemas,
        test_websocket_manager,
        test_config
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   [FAIL] FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    if failed == 0:
        print("\n[OK] All tests passed! The application components are working correctly.")
        print("\nNext steps:")
        print("1. Set up PostgreSQL and Redis (locally or via Docker)")
        print("2. Run: python scripts/train_model.py")
        print("3. Run: uvicorn app.main:app --reload")
        print("4. Access API docs at: http://localhost:8000/docs")
        return True
    else:
        print(f"\n[FAIL] {failed} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
