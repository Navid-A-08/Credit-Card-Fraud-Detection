#!/usr/bin/env python
"""
Simple test to verify basic functionality
"""

import sys
sys.path.append(0)

print("Testing imports...")

try:
    from app.config import settings
    print("[OK] Config imported")
except Exception as e:
    print(f"[FAIL] Config import failed: {e}")

try:
    from app.ml.features import FeatureEngineer
    print("[OK] FeatureEngineer imported")
except Exception as e:
    print(f"[FAIL] FeatureEngineer import failed: {e}")

try:
    from app.ml.model import FraudDetectionModel
    print("[OK] FraudDetectionModel imported")
except Exception as e:
    print(f"[FAIL] FraudDetectionModel import failed: {e}")

try:
    from app.schemas.transaction import TransactionCreate
    print("[OK] TransactionCreate imported")
except Exception as e:
    print(f"[FAIL] TransactionCreate import failed: {e}")

print("\nTesting feature extraction...")

try:
    fe = FeatureEngineer()
    transaction = {
        "amount": 100.0,
        "merchant_category": "online"
    }
    features = fe.extract_features(transaction)
    print(f"[OK] Features extracted: shape={features.shape}")
except Exception as e:
    print(f"[FAIL] Feature extraction failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting model creation...")

try:
    model = FraudDetectionModel(input_dim=12)
    print("[OK] Model created")
except Exception as e:
    print(f"[FAIL] Model creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting schema validation...")

try:
    data = {
        "transaction_id": "TXN123",
        "card_number": "4111111111111111",
        "amount": 100.0,
        "merchant_id": "M001",
        "merchant_name": "Test Store",
        "merchant_category": "retail"
    }
    transaction = TransactionCreate(**data)
    print(f"[OK] Schema validated: {transaction.transaction_id}")
except Exception as e:
    print(f"[FAIL] Schema validation failed: {e}")
    import traceback
    traceback.print_exc()

print("\nAll basic tests completed!")
