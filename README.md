# Real-Time Credit Card Fraud Detection API

A production-grade real-time credit card fraud detection system with live monitoring capabilities built with FastAPI, PostgreSQL, Redis, TensorFlow, and WebSockets.

## Features

- **Real-time Transaction Processing** - Analyze transactions in <100ms
- **ML-Powered Fraud Detection** - TensorFlow model with rule-based fallback
- **Live WebSocket Monitoring** - Real-time alerts and transaction streaming
- **Comprehensive REST API** - Full CRUD operations for transactions and alerts
- **PostgreSQL + Redis** - Persistent storage with caching and real-time features
- **Docker Ready** - Complete containerized deployment setup

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  REST API  │  WebSocket Manager  │  ML Inference Engine    │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL (Persistence)  │  Redis (Caching + Pub/Sub)    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Option 1: Docker (Recommended)

1. Clone the repository
2. Start all services:

```bash
docker-compose up -d
```

3. Access the API:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws/monitor
   - Celery Flower: http://localhost:5555

### Option 2: Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start PostgreSQL and Redis (or use Docker):

```bash
docker-compose up -d db redis
```

4. Run database migrations:

```bash
alembic upgrade head
```

5. Train the ML model:

```bash
python scripts/train_model.py
```

6. Start the API server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Transactions

- **POST /api/v1/transactions** - Create new transaction
- **GET /api/v1/transactions** - List transactions with filtering
- **GET /api/v1/transactions/{id}** - Get transaction details
- **GET /api/v1/transactions/stats/overview** - Transaction statistics

### Alerts

- **GET /api/v1/alerts** - List fraud alerts
- **GET /api/v1/alerts/{id}** - Get alert details
- **PUT /api/v1/alerts/{id}** - Update alert status
- **GET /api/v1/alerts/stats/overview** - Alert statistics

### Monitoring

- **GET /api/v1/monitoring/dashboard** - Dashboard data
- **GET /api/v1/monitoring/realtime** - Real-time metrics
- **WebSocket /ws/monitor** - Live transaction/alert stream

### Health

- **GET /api/v1/health** - System health check
- **GET /api/v1/stats** - System statistics

## Usage Examples

### Submit a Transaction

```bash
curl -X POST "http://localhost:8000/api/v1/transactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN123456",
    "card_number": "4111111111111111",
    "amount": 150.00,
    "merchant_id": "MERCHANT001",
    "merchant_name": "Amazon",
    "merchant_category": "online",
    "location_lat": 40.7128,
    "location_lon": -74.0060
  }'
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  if (data.type === 'transaction') {
    console.log('New transaction:', data.data);
  } else if (data.type === 'alert') {
    console.log('Fraud alert:', data.data);
  }
};

// Send ping to keep connection alive
ws.send(JSON.stringify({ type: 'ping' }));
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

Key configuration options:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ML_MODEL_PATH` - Path to TensorFlow model
- `FRAUD_THRESHOLD` - Score threshold for fraud detection (default: 0.7)
- `JWT_SECRET_KEY` - Secret key for JWT authentication

## ML Model

The fraud detection system uses a TensorFlow neural network with the following features:

- Transaction amount and patterns
- Time-based features (hour, day, weekend/night)
- Merchant category risk scoring
- Historical transaction velocity
- Geographic location analysis

### Model Performance

After training on synthetic data:

- Accuracy: ~95%
- Precision: ~90%
- Recall: ~85%
- F1 Score: ~87%

### Retraining

To retrain the model with new data:

```bash
python scripts/train_model.py
```

Or via API:

```bash
curl -X POST "http://localhost:8000/api/v1/model/retrain"
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
black app/
flake8 app/
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Production Deployment

### Environment Variables

Set these in production:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=your-secure-random-key
FRAUD_THRESHOLD=0.7
```

### Security Considerations

1. Change `JWT_SECRET_KEY` to a secure random value
2. Use HTTPS in production
3. Configure CORS for your domain
4. Set up proper authentication
5. Enable rate limiting

### Scaling

- Horizontal scaling: Run multiple API instances behind a load balancer
- Database: Use read replicas for query distribution
- Redis: Use Redis Cluster for high availability
- ML Model: Use model serving infrastructure (TensorFlow Serving)

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/api/v1/health
```

### Metrics

- Transaction processing rate
- Fraud detection accuracy
- API response times
- WebSocket connection count
- Alert generation rate

## License

This project is proprietary. All rights reserved.

## Support

For issues and questions:

- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the logs for debugging
