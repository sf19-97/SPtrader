# SPtrader Lazy Loading System
*Created: May 25, 2025 23:09 UTC*

## 🎯 Overview

SPtrader's lazy loading system automatically fetches missing forex data on-demand, providing seamless access to historical data without manual intervention.

## 🏗️ Architecture

### Components

1. **DataManager Service** (`internal/services/data_manager.go`)
   - Checks data availability in QuestDB
   - Identifies gaps in historical data coverage
   - Triggers background data fetching
   - Prevents duplicate fetch operations

2. **API Handlers** (`internal/api/data_handlers.go`)
   - RESTful endpoints for lazy loading operations
   - Integration with existing candle endpoints
   - Status monitoring and reporting

3. **ILP Integration**
   - Uses existing ILP infrastructure for data loading
   - High-performance batch inserts via port 9009
   - Automatic OHLC generation after tick loading

## 📡 API Endpoints

### Check Data Availability
```bash
GET /api/v1/data/check?symbol=EURUSD&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z
```

**Response:**
```json
{
  "symbol": "EURUSD",
  "first_tick": "2024-01-01T08:00:00Z",
  "last_tick": "2024-01-01T20:00:00Z", 
  "tick_count": 15420,
  "has_data": true,
  "gaps": [
    {
      "start": "2024-01-01T20:00:00Z",
      "end": "2024-01-02T00:00:00Z",
      "hours": 4
    }
  ]
}
```

### Ensure Data Exists
```bash
POST /api/v1/data/ensure
Content-Type: application/json

{
  "symbol": "GBPUSD",
  "start": "2024-01-01T00:00:00Z", 
  "end": "2024-01-02T00:00:00Z"
}
```

**Response:**
```json
{
  "status": "fetching",
  "message": "Data fetch initiated in background",
  "check_url": "/api/v1/data/status?symbol=GBPUSD"
}
```

### Smart Candles with Auto-Fetch
```bash
GET /api/v1/candles/lazy?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z
```

**Responses:**
- `200 OK` - Full data available, returns candles immediately
- `206 Partial Content` - Some data available, indicates gaps
- `202 Accepted` - No data available, use `/data/ensure` to fetch

### Data Status Monitoring
```bash
GET /api/v1/data/status
```

**Response:**
```json
{
  "total_ticks": 78175,
  "symbols": [
    {
      "symbol": "EURUSD",
      "tick_count": 78175,
      "first_tick": "2024-01-19T00:00:00Z",
      "last_tick": "2024-01-23T23:59:59Z",
      "days": 5
    }
  ],
  "updated_at": "2024-01-25T23:09:00Z"
}
```

## 🔄 Workflow

### Frontend Integration
```javascript
// Frontend requests data
const response = await fetch('/api/v1/candles/lazy?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z');

if (response.status === 200) {
  // Data available immediately
  const candles = await response.json();
  renderChart(candles);
  
} else if (response.status === 202) {
  // Data being fetched
  showLoadingIndicator();
  
  // Poll for completion or use WebSocket
  const pollData = setInterval(async () => {
    const retry = await fetch(originalUrl);
    if (retry.status === 200) {
      clearInterval(pollData);
      const candles = await retry.json();
      renderChart(candles);
    }
  }, 2000);
  
} else if (response.status === 206) {
  // Partial data available
  const partial = await response.json();
  renderChart(partial.candles);
  showGapIndicators(partial.gaps);
}
```

### Backend Process
1. **Request Analysis**
   - Parse symbol, timeframe, start/end dates
   - Calculate optimal resolution for viewport

2. **Data Availability Check**
   - Query QuestDB for tick data in range
   - Identify hourly gaps using time-bucket analysis
   - Skip weekends (forex market closed)

3. **Gap Handling**
   - If gaps found: Trigger background fetch
   - Use dukascopy_to_ilp.py for historical data
   - Prevent duplicate fetches with mutex locks

4. **Data Processing**
   - Load ticks via ILP (port 9009)
   - Generate OHLC aggregations automatically
   - Update data availability cache

## 🔧 Implementation Details

### Gap Detection Algorithm
```sql
-- Find hourly coverage gaps
SELECT 
  date_trunc('hour', timestamp) as hour,
  COUNT(*) as tick_count
FROM market_data_v2
WHERE symbol = $1 
  AND timestamp >= $2 
  AND timestamp <= $3
GROUP BY hour
ORDER BY hour
```

### Fetch Prevention
- Uses `sync.RWMutex` to prevent concurrent fetches
- Tracks ongoing operations by symbol+date key
- Automatic cleanup on completion/error

### Data Sources
- **Dukascopy**: Historical tick data (primary)
- **Oanda**: Real-time feed (future integration)
- **ILP Loading**: High-performance batch inserts

## 📊 Performance Characteristics

- **Gap Detection**: ~5-10ms per query
- **Data Fetching**: ~37,000 ticks/second via ILP
- **OHLC Generation**: ~2-3 seconds for 70K ticks
- **Memory Usage**: <50MB per active fetch

## 🚨 Error Handling

### Common Scenarios
1. **Network Failures**: Retry with exponential backoff
2. **Data Source Unavailable**: Graceful degradation 
3. **QuestDB Connection**: Connection pool retry
4. **Invalid Date Ranges**: Validation with helpful messages

### Monitoring
- Log all fetch operations with timing
- Track success/failure rates
- Monitor memory usage during fetches
- Alert on repeated failures

## 🎯 Frontend Integration Strategy

### Phase 1: Basic Integration
- Use `/candles/lazy` for all data requests
- Handle 202 responses with loading indicators
- Show gaps visually on charts

### Phase 2: Smart Loading
- Pre-fetch adjacent time ranges
- Background loading for viewport changes
- Intelligent caching of user navigation patterns

### Phase 3: Real-time Updates
- WebSocket integration for live data
- Incremental updates for recent data
- Conflict resolution for overlapping fetches

## 🛠️ Development Guidelines

### Adding New Data Sources
1. Implement fetcher interface in DataManager
2. Add source parameter to API endpoints
3. Update gap detection for source-specific logic
4. Test with small date ranges first

### Testing
```bash
# Test data availability
curl "http://localhost:8080/api/v1/data/check?symbol=GBPUSD&start=2024-03-01T00:00:00Z&end=2024-03-02T00:00:00Z"

# Trigger background fetch
curl -X POST "http://localhost:8080/api/v1/data/ensure" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"GBPUSD","start":"2024-03-01T00:00:00Z","end":"2024-03-02T00:00:00Z"}'

# Check fetch progress
sptrader logs -f

# Verify data loaded
sptrader db query "SELECT COUNT(*) FROM market_data_v2 WHERE symbol='GBPUSD'"
```

## 📚 Related Documentation

- `docs/ILP_IMPLEMENTATION.md` - Data ingestion details
- `PROJECT_STATUS.md` - Current implementation status
- `docs/SESSION_CHANGELOG.md` - Recent changes
- `CLAUDE.md` - Project-specific instructions

---

**Status**: ✅ Implemented and ready for frontend integration
**Next**: Build React frontend with lazy loading support