from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    FLAGGED = "flagged"


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=50)
    card_number: str = Field(..., min_length=13, max_length=16)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    merchant_id: str = Field(..., min_length=1, max_length=50)
    merchant_name: str = Field(..., min_length=1, max_length=255)
    merchant_category: str = Field(..., min_length=1, max_length=50)
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lon: Optional[float] = Field(None, ge=-180, le=180)

    @validator('card_number')
    def validate_card_number(cls, v):
        if not v.isdigit():
            raise ValueError('Card number must contain only digits')
        return v


class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    card_number: str
    amount: float
    currency: str
    merchant_id: str
    merchant_name: str
    merchant_category: str
    location_lat: Optional[float]
    location_lon: Optional[float]
    status: TransactionStatus
    fraud_score: float
    is_fraud: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionStats(BaseModel):
    total_transactions: int
    total_fraud: int
    fraud_rate: float
    average_amount: float
    average_fraud_score: float
    transactions_last_hour: int
    fraud_last_hour: int
