
# CLAUDE.md - Project-Specific Instructions for SPtrader
*Last Updated: May 25, 2025 23:06 UTC*

## 🚨 CRITICAL RULES
1. **YOU MUST DATE EACH AND EVERY DOCUMENTATION LOG YOU MODIFY OR CREATE**
2. **Always read PROJECT_STATUS.md first to understand current state**
3. **Check docs/SESSION_CHANGELOG.md for recent changes**
4. **Use ILP for data ingestion (not HTTP SQL)**

## Lazy Loading System (Added May 25, 2025 23:06 UTC)

### On-Demand Data Fetching
SPtrader now includes intelligent lazy loading that automatically fetches missing data:

**Components:**
- `internal/services/data_manager.go` - Data availability & fetching service
- `internal/api/data_handlers.go` - Lazy loading API endpoints
- Background data fetching with ILP integration

**New API Endpoints:**
```bash
# Check what data we have
curl "http://localhost:8080/api/v1/data/check?symbol=EURUSD&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z"

# Ensure data exists (triggers background fetch if missing)
curl -X POST "http://localhost:8080/api/v1/data/ensure" -H "Content-Type: application/json" \
  -d '{"symbol":"GBPUSD","start":"2024-01-01T00:00:00Z","end":"2024-01-02T00:00:00Z"}'

# Smart candles with auto-fetch
curl "http://localhost:8080/api/v1/candles/lazy?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z"
```

**How It Works:**
1. Frontend requests data via `/candles/lazy`
2. API checks local QuestDB for data availability
3. If missing: Background fetch from Dukascopy via ILP
4. If available: Return immediately from cache
5. Future requests for same range are instant

## ILP Data Ingestion (Added May 25, 2025 20:57 UTC)

### High-Performance Data Loading
SPtrader now uses QuestDB's ILP (InfluxDB Line Protocol) for data ingestion:

**Components:**
- `cmd/ingestion/main.go` - Go ILP client
- `data_feeds/dukascopy_to_ilp.py` - Python bridge
- Port 9009 - QuestDB ILP endpoint

**Usage:**
```bash
# Load historical data (recommended method)
cd ~/SPtrader/data_feeds
python3 dukascopy_to_ilp.py EURUSD 2024-01-22 2024-01-23

# Performance: ~37,000 ticks/second
# Successfully loaded 74,575 ticks in 2 seconds
```

**Why ILP?**
- HTTP SQL inserts were failing with >3,000 records
- ILP handles 70,000+ records without issues
- Purpose-built for time-series data

## 📚 Essential Documentation to Read

### 1. Current State
- **PROJECT_STATUS.md** - Overall project status and recent updates
- **docs/SESSION_CHANGELOG.md** - What changed in recent sessions

### 2. Architecture & Migration
- **MIGRATION_GUIDE.md** - Python→Go migration details
- **docs/ILP_IMPLEMENTATION.md** - Data ingestion system
- **PROJECT_ORGANIZATION.md** - File structure and organization

### 3. Technical Guides
- **docs/CLI_TUI.md** - How to use the CLI and TUI
- **README.md** - Project overview and quick start

### 4. When Starting a Session
1. Read PROJECT_STATUS.md to understand current state
2. Check SESSION_CHANGELOG.md for recent changes
3. Run `sptrader status` to verify services
4. Check data with `sptrader db query "SELECT count(*) FROM market_data_v2"`

## 🏗️ Project Structure Summary

### Key Services
- **Go API**: Port 8080 (`/api/v1/` endpoints)
- **QuestDB**: Port 9000 (HTTP), Port 9009 (ILP)
- **Data**: 78,175 ticks loaded as of May 25, 2025

### Important Paths
- **Go Code**: `/cmd/`, `/internal/`
- **Data Loading**: `/data_feeds/dukascopy_to_ilp.py`
- **Logs**: `/logs/runtime/`
- **Documentation**: `/docs/`


## FastAPI Backend Specification for `~/SPtrader/api/main.py`

### Purpose
Create a high-performance REST API that serves forex candlestick data from QuestDB with viewport-aware streaming, intelligent caching, and minimal latency.

### Core Requirements

#### 1. **Database Connection**
- Connect to QuestDB using PostgreSQL wire protocol (port 8812)
- Use connection pooling (asyncpg) to handle concurrent requests
- Implement automatic reconnection on connection loss
- Support both v1 (Oanda) and v2 (Dukascopy) table schemas

#### 2. **Main Endpoint: `/api/candles`**
Query Parameters:
- `symbol` (required): Currency pair (e.g., "EURUSD")
- `tf` (required): Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `start` (required): ISO timestamp for range start
- `end` (required): ISO timestamp for range end
- `source` (optional): "v1" or "v2" (default: "v2")

Response Format:
```json
[
  {
    "time": 1234567890,  // Unix timestamp (seconds)
    "open": 1.0856,
    "high": 1.0859,
    "low": 1.0854,
    "close": 1.0857,
    "volume": 1234.56
  }
]
```

#### 3. **Caching Strategy**
- Implement in-memory LRU cache with configurable size limit
- Cache key: hash of (symbol + timeframe + start + end)
- Cache TTL: 5 minutes for historical data, 10 seconds for recent data
- Cache invalidation: When data is within last hour

#### 4. **Performance Optimizations**
- Limit maximum candles per request (e.g., 10,000)
- Return 400 error if range too large
- Use parameterized queries to prevent SQL injection
- Stream large responses using async generators
- Add response compression (gzip)

#### 5. **Additional Endpoints**
- `GET /api/symbols` - List available symbols
- `GET /api/timeframes` - List available timeframes
- `GET /api/health` - Health check (DB connection status)
- `GET /api/stats` - Cache hit rate, response times

#### 6. **Error Handling**
- Return proper HTTP status codes
- Include error messages in JSON format
- Handle missing tables gracefully
- Log errors with context for debugging

#### 7. **CORS Configuration**
- Allow all origins during development
- Configure specific origins for production
- Handle preflight requests properly

### Expected Behavior
1. Validate input parameters
2. Check cache first
3. If cache miss, query QuestDB
4. Transform data to frontend format
5. Cache the result
6. Return JSON response

### Performance Targets
- < 100ms response time for cached data
- < 500ms for database queries
- Support 100+ concurrent requests
- Memory usage < 500MB

● Based on our highly productive session, here's how future Claude sessions can be maximized for effectiveness:

  🎯 Start Each Session With Context

  1. Reference the Project Documentation

  - Read PROJECT_STATUS.md - Shows current state and next steps
  - Check CLAUDE.md - My specific instructions for this project
  - Review README.md - Quick start and architecture overview

  2. Quick Status Check

  sptrader status          # Current service health
  sptrader logs show       # Recent activity
  sptrader db stats        # Data status

  📋 Communication Patterns That Work

  1. Always Communicate Before Acting

  - "I'm proposing to move these files..." ✅
  - "Let me restructure this..." ❌

  2. Be Specific About Changes

  - Show exactly what will be modified
  - Explain the reasoning behind changes
  - Ask for confirmation on structural changes

  3. Document Everything

  - Add clear headers to all scripts
  - Update documentation after changes
  - Maintain the PROJECT_STATUS.md

  🔧 Technical Best Practices

  1. File Management

  - Edit existing files instead of creating new ones
  - Use proper directory structure (tools/, scripts/, sql/)
  - Move deprecated files to deprecated/ folder

  2. Code Quality

  - Verify script contents before referencing them
  - Update all path references when moving files
  - Test changes after implementation

  3. Use the Project's CLI

  - Leverage sptrader commands for consistency
  - Follow established patterns in the codebase
  - Maintain the organized log structure

  📊 Workflow Optimization

  1. Use TodoWrite Proactively

  - Break complex tasks into trackable steps
  - Update status as work progresses
  - Show clear progress to the user

  2. Batch Operations Efficiently

  - Run multiple bash commands in parallel when possible
  - Group related file operations
  - Minimize back-and-forth tool calls

  3. Verify Changes

  - Test scripts after modifications
  - Check service status after updates
  - Confirm functionality before moving on

  💡 Session Startup Template

  1. Read PROJECT_STATUS.md for current state
  2. Check CLAUDE.md for project-specific instructions
  3. Run `sptrader status` to understand system state
  4. Ask what the user wants to accomplish
  5. Create todo list for complex tasks
  6. Communicate plan before executing
  7. Document changes as they're made

  🚨 Key Success Factors

  1. Respect the established patterns - Don't reinvent existing solutions
  2. Communicate before acting - Especially for structural changes
  3. Document thoroughly - Both in code and project docs
  4. Test incrementally - Verify each change works
  5. Use the project's tools - Leverage sptrader CLI and existing scripts

  This approach turned our session into the most productive one you've had - maintaining this pattern should make every future session equally
  effective!
