from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.models.database import get_db
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertUpdate,
    AlertStats
)

router = APIRouter()


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Alert)
    count_query = select(func.count(Alert.id))

    # Apply filters
    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)

    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)

    if start_date:
        query = query.where(Alert.created_at >= start_date)
        count_query = count_query.where(Alert.created_at >= start_date)

    if end_date:
        query = query.where(Alert.created_at <= end_date)
        count_query = count_query.where(Alert.created_at <= end_date)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Alert.created_at.desc())

    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=alerts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields
    if alert_update.status is not None:
        alert.status = alert_update.status
        if alert_update.status == AlertStatus.RESOLVED:
            alert.resolved_at = datetime.utcnow()

    if alert_update.notes is not None:
        alert.notes = alert_update.notes

    if alert_update.assigned_to is not None:
        alert.assigned_to = alert_update.assigned_to

    await db.flush()
    await db.refresh(alert)

    return alert


@router.get("/stats/overview", response_model=AlertStats)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    one_hour_ago = now.replace(minute=now.minute - 1) if now.minute > 0 else now.replace(hour=now.hour - 1, minute=59)

    # Total alerts
    total_query = select(func.count(Alert.id))
    total_result = await db.execute(total_query)
    total_alerts = total_result.scalar()

    # Open alerts
    open_query = select(func.count(Alert.id)).where(Alert.status == AlertStatus.OPEN)
    open_result = await db.execute(open_query)
    open_alerts = open_result.scalar()

    # Investigating alerts
    investigating_query = select(func.count(Alert.id)).where(Alert.status == AlertStatus.INVESTIGATING)
    investigating_result = await db.execute(investigating_query)
    investigating_alerts = investigating_result.scalar()

    # Resolved alerts
    resolved_query = select(func.count(Alert.id)).where(Alert.status == AlertStatus.RESOLVED)
    resolved_result = await db.execute(resolved_query)
    resolved_alerts = resolved_result.scalar()

    # Alerts by severity
    severity_stats = {}
    for severity in AlertSeverity:
        severity_query = select(func.count(Alert.id)).where(Alert.severity == severity)
        severity_result = await db.execute(severity_query)
        severity_stats[severity.value] = severity_result.scalar()

    # Alerts last hour
    last_hour_query = select(func.count(Alert.id)).where(Alert.created_at >= one_hour_ago)
    last_hour_result = await db.execute(last_hour_query)
    alerts_last_hour = last_hour_result.scalar()

    return AlertStats(
        total_alerts=total_alerts,
        open_alerts=open_alerts,
        investigating_alerts=investigating_alerts,
        resolved_alerts=resolved_alerts,
        alerts_by_severity=severity_stats,
        alerts_last_hour=alerts_last_hour
    )
