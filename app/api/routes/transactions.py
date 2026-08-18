from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, timedelta
import json

from app.models.database import get_db
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    TransactionStats
)
from app.services.fraud_detection import FraudDetectionService
from app.api.websockets import get_websocket_manager, ConnectionManager

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    fraud_service: FraudDetectionService = Depends(FraudDetectionService),
    ws_manager: ConnectionManager = Depends(get_websocket_manager)
):
    # Create transaction record
    db_transaction = Transaction(
        transaction_id=transaction.transaction_id,
        card_number=transaction.card_number,
        amount=transaction.amount,
        currency=transaction.currency,
        merchant_id=transaction.merchant_id,
        merchant_name=transaction.merchant_name,
        merchant_category=transaction.merchant_category,
        location_lat=transaction.location_lat,
        location_lon=transaction.location_lon
    )

    # Perform fraud detection
    fraud_score, features = await fraud_service.analyze_transaction(transaction)
    db_transaction.fraud_score = fraud_score
    db_transaction.features_json = json.dumps(features)

    # Determine status based on fraud score
    if fraud_score >= 0.8:
        db_transaction.status = TransactionStatus.DECLINED
        db_transaction.is_fraud = True
    elif fraud_score >= 0.6:
        db_transaction.status = TransactionStatus.FLAGGED
    else:
        db_transaction.status = TransactionStatus.APPROVED

    db.add(db_transaction)
    await db.flush()
    await db.refresh(db_transaction)

    # Broadcast transaction via WebSocket
    await ws_manager.broadcast_transaction({
        "id": db_transaction.id,
        "transaction_id": db_transaction.transaction_id,
        "amount": db_transaction.amount,
        "merchant_name": db_transaction.merchant_name,
        "status": db_transaction.status.value,
        "fraud_score": db_transaction.fraud_score
    })

    # If high fraud score, create alert
    if fraud_score >= 0.6:
        from app.services.alert_service import AlertService
        alert_service = AlertService()
        await alert_service.create_alert_from_transaction(db_transaction, db)

    return db_transaction


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TransactionStatus] = None,
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    # Build query
    query = select(Transaction)
    count_query = select(func.count(Transaction.id))

    # Apply filters
    if status:
        query = query.where(Transaction.status == status)
        count_query = count_query.where(Transaction.status == status)

    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
        count_query = count_query.where(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
        count_query = count_query.where(Transaction.amount <= max_amount)

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
        count_query = count_query.where(Transaction.created_at >= start_date)

    if end_date:
        query = query.where(Transaction.created_at <= end_date)
        count_query = count_query.where(Transaction.created_at <= end_date)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Transaction.created_at.desc())

    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.get("/stats/overview", response_model=TransactionStats)
async def get_transaction_stats(
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # Total transactions
    total_query = select(func.count(Transaction.id))
    total_result = await db.execute(total_query)
    total_transactions = total_result.scalar()

    # Total fraud
    fraud_query = select(func.count(Transaction.id)).where(Transaction.is_fraud == True)
    fraud_result = await db.execute(fraud_query)
    total_fraud = fraud_result.scalar()

    # Average amount
    avg_amount_query = select(func.avg(Transaction.amount))
    avg_amount_result = await db.execute(avg_amount_query)
    average_amount = avg_amount_result.scalar() or 0.0

    # Average fraud score
    avg_score_query = select(func.avg(Transaction.fraud_score))
    avg_score_result = await db.execute(avg_score_query)
    average_fraud_score = avg_score_result.scalar() or 0.0

    # Transactions last hour
    last_hour_query = select(func.count(Transaction.id)).where(
        Transaction.created_at >= one_hour_ago
    )
    last_hour_result = await db.execute(last_hour_query)
    transactions_last_hour = last_hour_result.scalar()

    # Fraud last hour
    fraud_last_hour_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.created_at >= one_hour_ago,
            Transaction.is_fraud == True
        )
    )
    fraud_last_hour_result = await db.execute(fraud_last_hour_query)
    fraud_last_hour = fraud_last_hour_result.scalar()

    return TransactionStats(
        total_transactions=total_transactions,
        total_fraud=total_fraud,
        fraud_rate=total_fraud / total_transactions if total_transactions > 0 else 0.0,
        average_amount=average_amount,
        average_fraud_score=average_fraud_score,
        transactions_last_hour=transactions_last_hour,
        fraud_last_hour=fraud_last_hour
    )
