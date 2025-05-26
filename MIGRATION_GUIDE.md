# SPtrader Migration Guide: Python → Go
*Last Updated: May 25, 2025 20:54 UTC*

## 🔄 Migration Status

We are transitioning SPtrader from Python (FastAPI) to Go (Gin) for better performance, type safety, and cleaner architecture.

### Current State (May 25, 2025)
- **Python API**: ❌ DEPRECATED - moved to `/deprecated/python-api/`
- **Go API**: ✅ RUNNING - port 8080 (primary)
- **Database**: ✅ Connected with `?sslmode=disable`
- **CLI**: ✅ UPDATED - using Go API on port 8080
- **TUI**: ✅ UPDATED - calls CLI commands

## 📁 Directory Organization

### Root Directory Files

#### Active Entry Points
- `sptrader` - Main CLI (✅ updated to use Go API)
- `clean_tui.py` - Current TUI interface
- `SPtrader-login.py` - Matrix authentication wrapper

#### Build Files (Go)
- `go.mod` - Go module definition
- `go.sum` - Go dependency locks
- `Makefile` - Build automation for Go
- `.env.example` - Configuration template

#### Legacy Files (To Be Moved)
- `sexy_minimal_tui.py` - Old TUI (move to `/deprecated`)
- `matrix_tui.py` - Old TUI attempt (move to `/deprecated`)
- `start_go_services.sh` - Current start script (✅ replaced old Python script)
- `stop_all.sh` - Works for both Python and Go

### New Go Structure
```
cmd/
├── api/          # Main API application
└── profiler/     # Performance profiling tool

internal/         # Private Go packages
├── api/          # HTTP handlers
├── config/       # Configuration
├── db/           # Database layer
├── models/       # Domain models
└── services/     # Business logic

build/           # Compiled binaries (git-ignored)
```

### Existing Python Structure (Unchanged)
```
api/             # Python FastAPI (being replaced)
data_feeds/      # Data importers (staying Python for now)
scripts/         # Utility scripts (mixed Python/Bash)
tools/           # Management tools
```

## 🚀 Migration Steps

### Phase 1: Parallel Running (✅ COMPLETED)
```bash
# Migration complete - only Go API runs now
./start_go_services.sh     # Starts Go API on :8080
# or
sptrader start            # Preferred method
```

### Phase 2: Switch Default (✅ COMPLETED)
The migration scripts have been run and moved to `/deprecated/migration-scripts/`:
- ✅ sptrader CLI now points to :8080
- ✅ API paths updated to /api/v1/
- ✅ Start scripts use Go binary

### Phase 3: Cleanup (🔄 IN PROGRESS)
```bash
# Move old files
mkdir -p deprecated/python-api
mv api/ deprecated/python-api/
mv sexy_minimal_tui.py deprecated/
mv matrix_tui.py deprecated/

# Update documentation
mv README.md README_LEGACY.md
mv README_GO.md README.md
```

## 📊 API Compatibility

### Endpoint Mapping

| Python (Old) | Go (New) | Notes |
|-------------|----------|-------|
| `/api/health` | `/api/v1/health` | Same response format |
| `/api/candles` | `/api/v1/candles` | Same parameters |
| - | `/api/v1/candles/smart` | NEW: Auto resolution |
| - | `/api/v1/candles/explain` | NEW: Query planning |
| `/api/symbols` | `/api/v1/symbols` | Enhanced response |
| `/api/stats` | `/api/v1/stats` | Different metrics |
| - | `/api/v1/contract` | NEW: Data contract |

### Parameter Changes
- `tf` → `timeframe` (both accepted)
- `source` still accepts "v1" or "v2"
- NEW: `resolution` parameter for manual override

## 🧪 Testing During Migration

### 1. Compare Responses
```bash
# Same query to both APIs
curl "http://localhost:8000/api/candles?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z" > python_response.json

curl "http://localhost:8080/api/v1/candles?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z" > go_response.json

# Compare (structure might differ slightly)
jq . python_response.json
jq . go_response.json
```

### 2. Performance Comparison
```bash
# Python API
time curl "http://localhost:8000/api/candles?..."

# Go API  
time curl "http://localhost:8080/api/v1/candles?..."
```

### 3. Load Testing
```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test Python
hey -n 1000 -c 10 "http://localhost:8000/api/candles?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z"

# Test Go
hey -n 1000 -c 10 "http://localhost:8080/api/v1/candles?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z"
```

## 📝 Configuration Changes

### Environment Variables
Python uses different var names than Go:

| Python | Go | Purpose |
|--------|-----|---------|
| `QUESTDB_HOST` | `DATABASE_URL` | Database connection |
| `API_PORT` | `SERVER_ADDRESS` | Listen address |
| - | `GIN_MODE` | debug/release mode |

### Frontend Updates
```javascript
// Old Python API
const API_BASE = 'http://localhost:8000/api';

// New Go API
const API_BASE = 'http://localhost:8080/api/v1';

// Or use smart endpoint
fetch(`${API_BASE}/candles/smart?symbol=EURUSD&start=${start}&end=${end}`)
  .then(res => res.json())
  .then(data => {
    // API automatically selected best resolution
    console.log(`Using ${data.resolution} resolution`);
  });
```

## 🔍 Monitoring the Migration

### Check Service Status
```bash
# See what's running
ps aux | grep -E "(uvicorn|sptrader-api)"

# Check ports
netstat -tlnp | grep -E "(8000|8080)"
```

### Log Locations
- Python logs: `~/SPtrader/logs/fastapi.log`
- Go logs: `stdout` (use systemd or redirect)

## ⚠️ Breaking Changes

1. **API Base Path**: `/api/` → `/api/v1/`
2. **Default Port**: 8000 → 8080
3. **Cache Keys**: Different format (won't share cache)
4. **Error Responses**: Slightly different structure

## 🎯 Success Criteria

Migration is complete when:
- [x] Go API handles all production traffic
- [x] Performance baselines met (<100ms for viewport queries)
- [x] Frontend fully migrated to new endpoints
- [x] Python API disabled (moved to deprecated)
- [x] Documentation updated
- [x] Root directory cleaned up

## 🚨 Rollback Plan

If issues arise:
```bash
# Stop Go API
pkill sptrader-api

# Revert sptrader CLI
git checkout sptrader

# Restart Python API
./start_background.sh
```

## 🆕 Data Ingestion Enhancement (May 25, 2025 20:54 UTC)

### ILP Implementation
We've added high-performance data ingestion using QuestDB's ILP (InfluxDB Line Protocol):

**Components Added:**
- `cmd/ingestion/main.go` - Go ILP ingestion service
- `data_feeds/dukascopy_to_ilp.py` - Python-Go bridge
- Port 9009 - QuestDB ILP endpoint (vs 9000 for HTTP)

**Performance Improvement:**
- Old: HTTP SQL inserts failed with 3,761 records
- New: ILP successfully ingests 74,575 records in 2 seconds (~37,000/sec)

See `docs/ILP_IMPLEMENTATION.md` for details.

## 📚 Additional Documentation

- `docs/ILP_IMPLEMENTATION.md` - ILP ingestion guide (NEW)
- `README_GO.md` - Go API specific documentation
- `docs/PYTHON_VS_GO_COMPARISON.md` - Performance comparison
- `docs/DATA_ARCHITECTURE_PLAN.md` - Overall architecture
- `PROJECT_STATUS.md` - Current project state