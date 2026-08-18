from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertCreate(BaseModel):
    transaction_id: int
    fraud_score: float = Field(..., ge=0, le=1)
    reason: str = Field(..., min_length=1)
    severity: AlertSeverity


class AlertResponse(BaseModel):
    id: int
    transaction_id: int
    severity: AlertSeverity
    status: AlertStatus
    fraud_score: float
    reason: str
    notes: Optional[str]
    assigned_to: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus]
    notes: Optional[str]
    assigned_to: Optional[str]


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AlertStats(BaseModel):
    total_alerts: int
    open_alerts: int
    investigating_alerts: int
    resolved_alerts: int
    alerts_by_severity: dict
    alerts_last_hour: int
