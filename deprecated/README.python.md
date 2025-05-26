# SPtrader - High-Performance Forex Trading Platform (Go Edition)

A professional forex trading platform with real-time data feeds, high-performance charting, and viewport-aware data streaming.

**Now powered by Go!** - Migrated from Python for better performance, type safety, and concurrent handling.

## 🚀 Quick Start

### Prerequisites
- Go 1.21+ (installed)
- QuestDB (included)
- Some market data loaded

### Start Trading
```bash
sptrader start    # Start all services (Go API + QuestDB)
sptrader monitor  # Watch real-time dashboard
```

Visit:
- API Health: http://localhost:8080/api/v1/health
- Data Contract: http://localhost:8080/api/v1/contract
- QuestDB Console: http://localhost:9000

```bash
sptrader start    # Start all services
sptrader monitor  # Watch real-time dashboard
```

Visit http://localhost:8000/docs for API documentation.

## 📖 SPtrader CLI Guide

The `sptrader` command is your central control for the entire platform.

### Basic Commands

#### Service Management
```bash
sptrader start      # Start all services (QuestDB, API, feeds)
sptrader stop       # Stop all services gracefully
sptrader restart    # Restart all services
sptrader status     # Check what's running
```

#### Real-time Monitoring
```bash
sptrader monitor    # Interactive dashboard with:
                   # - Service status & memory usage
                   # - API statistics & cache hit rates
                   # - Live market prices
                   # - System resources
                   # Press: L=logs, S=stop, R=restart, Q=quit
```

#### Logs & Debugging
```bash
sptrader logs       # View recent logs from all services
sptrader logs -f    # Follow logs in real-time (like tail -f)
```

### API Management

```bash
sptrader api health   # Check if API is responding
sptrader api stats    # View cache hits, request counts, DB pool
sptrader api docs     # Open Swagger documentation
sptrader api test     # Run API test suite
```

### Database Operations

```bash
sptrader db console   # Open QuestDB web interface
sptrader db stats     # Quick data statistics

# Execute custom queries
sptrader db query 'SELECT count(*) FROM ohlc_5m_v2'
sptrader db query 'SELECT * FROM ohlc_1h_v2 WHERE symbol='\''EURUSD'\'' LIMIT 10'
```

### Performance Optimization

```bash
sptrader optimize    # Create viewport tables for fast zooming
sptrader test        # Run all tests (API + viewport)
```

## 📊 Architecture

### Services
- **QuestDB**: Time-series database (port 9000)
- **FastAPI**: REST API backend (port 8000)
- **React**: Frontend application (port 5173)
- **Oanda Feed**: Live market data
- **OHLC Manager**: Data aggregation

### Data Flow
```
Oanda/Dukascopy → QuestDB → FastAPI → React Charts
                     ↓
              Viewport Tables
              (optimized queries)
```

## 🔧 Common Tasks

### Check Market Data
```bash
# See how much data you have
sptrader db stats

# Check latest prices
sptrader monitor  # Look at "Latest Market Prices" section

# Query specific data
sptrader db query 'SELECT * FROM eurusd_5m_oanda ORDER BY timestamp DESC LIMIT 5'
```

### Troubleshooting
```bash
# If services won't start
sptrader status              # See what's wrong
sptrader logs                # Check error messages

# If API isn't responding
sptrader api health          # Check connection
sptrader logs -f             # Watch for errors

# Force restart everything
sptrader stop                # Stop all
ps aux | grep -E "(questdb|uvicorn|oanda)"  # Check stragglers
sptrader start               # Start fresh
```

### Monitor Performance
```bash
# In the monitor view, watch:
# - Cache Hit Rate (should be >50% after warmup)
# - DB Pool connections (should have free connections)
# - Memory usage per service
# - System CPU/Memory
```

## 📁 Project Structure

```
SPtrader/
├── api/                 # FastAPI backend
│   ├── main.py         # API endpoints
│   └── test_api.py     # API tests
├── frontend/           # React frontend (TBD)
├── data_feeds/         # Market data importers
├── scripts/            # Core services
├── tools/              # Management scripts
├── logs/               # Service logs
└── sptrader           # CLI wrapper
```

## 🌐 Service URLs

After `sptrader start`:
- **QuestDB Console**: http://localhost:9000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health
- **React Frontend**: http://localhost:5173 (when configured)

## 💡 Tips

1. **First Time Setup**: Run `sptrader optimize` after loading historical data
2. **Monitor Regularly**: Keep `sptrader monitor` open to watch system health
3. **Check Logs**: Use `sptrader logs -f` when debugging issues
4. **API Testing**: Use `sptrader api docs` to explore endpoints interactively

## 🚨 Important Notes

- Services take ~10-15 seconds to fully start
- QuestDB needs ~5 seconds before accepting connections
- Cache warms up after first few requests
- Viewport tables significantly improve zoom performance

## 📈 Next Steps - Data-First Approach

1. **Profile First**: Run `tools/profile_data_limits.py` with test data
2. **Build Data Contract**: Understand your performance boundaries
3. **Design UI Within Limits**: Chart behavior respects data capabilities
4. **Scale Gradually**: Test with increasing data volumes
5. **Optimize as Needed**: Consider Go service only if Python too slow

---

For detailed API documentation, visit http://localhost:8000/docs after starting services.

## 🏗️ Architecture (Go Implementation)

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
