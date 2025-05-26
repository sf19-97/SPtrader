# SPtrader Go API

High-performance Go implementation of the SPtrader API using Gin framework.

## 🚀 Quick Start

### Prerequisites
- Go 1.21 or later
- QuestDB running on port 8812
- Some test data loaded

### Build and Run
```bash
# Download dependencies
make deps

# Build the binary
make build

# Run in development
make dev

# Run tests
make test
```

## 📊 Architecture

### Clean Architecture Layers
```
cmd/
  api/          - Application entry point
  profiler/     - Data profiling tool
  
internal/
  api/          - HTTP handlers and middleware
  config/       - Configuration management
  db/           - Database connection pool
  models/       - Domain models
  services/     - Business logic
```

### Key Features
1. **Smart Resolution Selection** - Automatically picks optimal table based on time range
2. **Viewport-Aware Queries** - Uses pre-aggregated tables for performance
3. **Intelligent Caching** - LRU cache with TTL based on data recency
4. **Data Contracts** - Enforced performance boundaries
5. **Connection Pooling** - Efficient database connections

## 🔧 Configuration

Create `.env` file:
```env
# Server
SERVER_ADDRESS=:8080
GIN_MODE=release

# Database
DATABASE_URL=postgres://admin:quest@localhost:8812/qdb
DB_MAX_CONNECTIONS=20

# Cache
CACHE_MAX_SIZE=1000
CACHE_TTL=5m
```

## 📡 API Endpoints

### Data Endpoints
- `GET /api/v1/candles` - Get candle data
- `GET /api/v1/candles/smart` - Smart resolution selection
- `GET /api/v1/candles/explain` - Explain query planning

### Market Data
- `GET /api/v1/symbols` - Available symbols
- `GET /api/v1/timeframes` - Supported timeframes

### Monitoring
- `GET /api/v1/health` - Health check
- `GET /api/v1/stats` - API statistics
- `GET /api/v1/contract` - Data contract

## 🏃 Performance

### Profiling Your Data
```bash
# Run the profiler to understand your data limits
go run cmd/profiler/main.go
```

This will:
1. Test query performance for each table
2. Find optimal time ranges for each resolution
3. Generate a data contract

### Expected Performance
- 1m data: < 50ms for 4 hours (240 points)
- 5m data: < 75ms for 1 day (288 points)
- 1h data: < 100ms for 1 week (168 points)
- 4h data: < 150ms for 1 month (180 points)
- 1d data: < 200ms for 1 year (365 points)

## 🔄 Migration from Python

```bash
# Run migration script
./scripts/migrate_to_go.sh

# This will:
# 1. Stop Python services
# 2. Build Go API
# 3. Update configuration
# 4. Create systemd service
```

## 🧪 Testing

```bash
# Unit tests
make test

# Integration tests with coverage
make test-coverage

# Load testing
go get -u github.com/rakyll/hey
hey -n 1000 -c 10 http://localhost:8080/api/v1/health
```

## 📈 Production Deployment

### Systemd Service
```bash
# Copy service file
sudo cp sptrader-api.service /etc/systemd/system/

# Enable and start
sudo systemctl enable sptrader-api
sudo systemctl start sptrader-api

# Check status
sudo systemctl status sptrader-api
```

### Docker
```bash
# Build image
make docker-build

# Run container
make docker-run
```

## 🎯 Design Principles

1. **Data-First** - Profile data limits, build UI to respect them
2. **Performance** - Every query should be < 100ms
3. **Type Safety** - Leverage Go's type system
4. **Clean Code** - Clear separation of concerns
5. **Observable** - Comprehensive logging and metrics

## 🔍 Debugging

### Enable Debug Logging
```bash
GIN_MODE=debug ./build/sptrader-api
```

### Check Query Planning
```bash
curl "http://localhost:8080/api/v1/candles/explain?symbol=EURUSD&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z"
```

### Monitor Database Pool
```bash
curl http://localhost:8080/api/v1/stats | jq .database_pool
```

## 📚 Frontend Integration

The API returns a data contract that the frontend should respect:

```javascript
// Fetch and use data contract
fetch('http://localhost:8080/api/v1/contract')
  .then(res => res.json())
  .then(contract => {
    // Use contract to determine:
    // - Maximum points to request
    // - Which resolution to use
    // - Performance expectations
  });
```

Example smart query:
```javascript
// Let the API choose the best resolution
fetch('/api/v1/candles/smart?symbol=EURUSD&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z')
  .then(res => res.json())
  .then(data => {
    console.log(`Got ${data.count} candles at ${data.resolution} resolution`);
    console.log(`Query took ${data.metadata.query_time_ms}ms`);
  });
```