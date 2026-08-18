#!/usr/bin/env python
"""
Minimal test without config dependencies
"""

import sys
sys.path.append(0)

print("Testing minimal functionality...")

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import numpy as np
    print("[OK] NumPy imported")
except Exception as e:
    print(f"[FAIL] NumPy: {e}")

try:
    import pandas as pd
    print("[OK] Pandas imported")
except Exception as e:
    print(f"[FAIL] Pandas: {e}")

# Test 2: TensorFlow
print("\n2. Testing TensorFlow...")
try:
    import tensorflow as tf
    print(f"[OK] TensorFlow {tf.__version__} imported")
except Exception as e:
    print(f"[FAIL] TensorFlow: {e}")

# Test 3: FastAPI
print("\n3. Testing FastAPI...")
try:
    from fastapi import FastAPI
    print("[OK] FastAPI imported")
except Exception as e:
    print(f"[FAIL] FastAPI: {e}")

# Test 4: SQLAlchemy
print("\n4. Testing SQLAlchemy...")
try:
    from sqlalchemy.ext.asyncio import create_async_engine
    print("[OK] SQLAlchemy imported")
except Exception as e:
    print(f"[FAIL] SQLAlchemy: {e}")

# Test 5: Pydantic
print("\n5. Testing Pydantic...")
try:
    from pydantic import BaseModel
    print("[OK] Pydantic imported")
except Exception as e:
    print(f"[FAIL] Pydantic: {e}")

# Test 6: Create a simple TensorFlow model
print("\n6. Testing TensorFlow model creation...")
try:
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=(12,)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print("[OK] TensorFlow model created")

    # Test prediction
    test_input = np.random.rand(1, 12).astype(np.float32)
    prediction = model.predict(test_input, verbose=0)
    print(f"[OK] Model prediction: {prediction[0][0]:.4f}")
except Exception as e:
    print(f"[FAIL] TensorFlow model: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Create FastAPI app
print("\n7. Testing FastAPI app creation...")
try:
    app = FastAPI(title="Test API")
    print("[OK] FastAPI app created")
except Exception as e:
    print(f"[FAIL] FastAPI app: {e}")

print("\n" + "="*50)
print("Minimal tests completed!")
print("="*50)
