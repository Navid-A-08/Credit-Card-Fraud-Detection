import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from typing import Tuple


class FraudDetectionModel:
    def __init__(self, input_dim: int = 12):
        self.input_dim = input_dim
        self.model = self._build_model()

    def _build_model(self) -> keras.Model:
        model = keras.Sequential([
            # Input layer
            layers.Dense(128, activation='relu', input_shape=(self.input_dim,)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            # Hidden layers
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(32, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),

            layers.Dense(16, activation='relu'),
            layers.Dropout(0.2),

            # Output layer
            layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=[
                'accuracy',
                keras.metrics.Precision(name='precision'),
                keras.metrics.Recall(name='recall'),
                keras.metrics.AUC(name='auc')
            ]
        )

        return model

    def summary(self):
        return self.model.summary()

    def get_model(self) -> keras.Model:
        return self.model

    def save_model(self, filepath: str):
        self.model.save(filepath)

    def load_model(self, filepath: str):
        self.model = keras.models.load_model(filepath)

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self.model.predict(features, verbose=0)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None,
        epochs: int = 50,
        batch_size: int = 32
    ):
        callbacks = [
            keras.callbacks.EarlyStopping(
                patience=5,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                factor=0.5,
                patience=2
            )
        ]

        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)

        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )

        return history
