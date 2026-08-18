from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from app.models.database import Base
import enum


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    FLAGGED = "flagged"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    card_number = Column(String(16), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    merchant_id = Column(String(50), nullable=False)
    merchant_name = Column(String(255), nullable=False)
    merchant_category = Column(String(50), nullable=False)
    location_lat = Column(Float)
    location_lon = Column(Float)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    fraud_score = Column(Float, default=0.0)
    is_fraud = Column(Boolean, default=False)
    features_json = Column(Text)  # JSON blob of engineered features
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transaction {self.transaction_id}: ${self.amount} - Score: {self.fraud_score}>"
