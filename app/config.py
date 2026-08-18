from typing import Optional
import os


class Settings:
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fraud_detection")
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "300"))

        # ML Model
        self.ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "./app/ml/models/fraud_detector.h5")
        self.FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.7"))

        # Security
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

        # WebSocket
        self.WEBSOCKET_HEARTBEAT_INTERVAL = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))

        # Celery
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")


settings = Settings()
