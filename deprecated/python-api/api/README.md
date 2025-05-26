# SPTrader API

High-performance REST API for serving forex candlestick data from QuestDB.

## Features

- ✅ FastAPI backend with async support
- ✅ Connection pooling for QuestDB
- ✅ Smart caching with LRU eviction
- ✅ Viewport-aware data streaming
- ✅ Input validation and error handling
- ✅ CORS support for frontend integration
- ✅ Health checks and statistics

## Installation

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Endpoints

### GET /api/candles
Get candlestick data for a specific symbol and timeframe.

Query parameters:
- `symbol` (required): Currency pair (e.g., "EURUSD")
- `tf` (required): Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `start` (required): ISO timestamp for range start
- `end` (required): ISO timestamp for range end
- `source` (optional): "v1" or "v2" (default: "v2")

### GET /api/symbols
List available currency pairs.

### GET /api/timeframes
List available timeframes.

### GET /api/health
Health check endpoint.

### GET /api/stats
Get cache and database statistics.

## Performance

- < 100ms response time for cached data
- < 500ms for database queries
- Supports 100+ concurrent requests
- Memory usage < 500MB

## Testing

```bash
python test_api.py
```