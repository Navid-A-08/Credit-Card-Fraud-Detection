import numpy as np
import os
from typing import Dict, Any
import tensorflow as tf

from app.config import settings
from app.ml.model import FraudDetectionModel
from app.ml.features import FeatureEngineer
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FraudPredictor:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(settings.ML_MODEL_PATH):
                self.model = FraudDetectionModel()
                self.model.load_model(settings.ML_MODEL_PATH)
                self.model_loaded = True
                logger.info(f"Loaded fraud detection model from {settings.ML_MODEL_PATH}")
            else:
                logger.warning(f"Model file not found at {settings.ML_MODEL_PATH}. Using default model.")
                self._create_default_model()
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._create_default_model()

    def _create_default_model(self):
        self.model = FraudDetectionModel(input_dim=12)
        self.model_loaded = False
        logger.info("Created default fraud detection model (untrained)")

    async def predict(self, features: Dict[str, Any]) -> float:
        try:
            # Convert features to numpy array
            feature_array = self.feature_engineer.extract_features(features)

            # Get prediction
            if self.model_loaded:
                prediction = self.model.predict(feature_array)
                fraud_score = float(prediction[0][0])
            else:
                # Fallback rule-based scoring when model is not trained
                fraud_score = self._rule_based_scoring(features)

            # Ensure score is between 0 and 1
            fraud_score = max(0.0, min(1.0, fraud_score))

            return fraud_score

        except Exception as e:
            logger.error(f"Error in fraud prediction: {e}")
            # Return moderate risk score on error
            return 0.5

    def _rule_based_scoring(self, features: Dict[str, Any]) -> float:
        score = 0.0

        # Amount-based scoring
        amount = features.get('amount', 0)
        if amount > 1000:
            score += 0.3
        elif amount > 500:
            score += 0.2
        elif amount > 100:
            score += 0.1

        # Time-based scoring
        if features.get('is_night', 0):
            score += 0.2

        # Category risk
        category_risk = features.get('category_risk', 0.5)
        score += category_risk * 0.3

        # Location risk
        if not features.get('has_location', 0):
            score += 0.1

        # Velocity checks
        if features.get('transaction_count_1h', 0) > 5:
            score += 0.3
        elif features.get('transaction_count_1h', 0) > 3:
            score += 0.2

        # Amount deviation
        avg_amount = features.get('avg_amount_24h', 0)
        if avg_amount > 0 and amount > avg_amount * 3:
            score += 0.4

        return min(1.0, score)

    async def retrain_model(self, training_data: np.ndarray, labels: np.ndarray):
        try:
            logger.info("Starting model retraining")

            # Split data
            split_idx = int(len(training_data) * 0.8)
            X_train = training_data[:split_idx]
            y_train = labels[:split_idx]
            X_val = training_data[split_idx:]
            y_val = labels[split_idx:]

            # Train model
            history = self.model.train(
                X_train, y_train,
                X_val, y_val,
                epochs=20,
                batch_size=32
            )

            # Save model
            self.model.save_model(settings.ML_MODEL_PATH)
            self.model_loaded = True

            logger.info("Model retraining completed successfully")
            return history

        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_path": settings.ML_MODEL_PATH,
            "input_dim": self.model.input_dim if self.model else None,
            "fraud_threshold": settings.FRAUD_THRESHOLD
        }
