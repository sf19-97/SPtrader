# SPtrader Data Architecture Plan
*Created: May 25, 2025*

## 🎯 Overview
This document outlines the data-first approach to building SPtrader's charting system. We'll establish data patterns, performance boundaries, and API contracts before implementing the frontend charts.

## 📊 Phase 1: Test Data Loading & Profiling

### 1.1 Initial Test Data Load
**Goal**: Load 1 week of EURUSD data to understand system behavior

```bash
# Start services
sptrader start

# Load test data
cd ~/SPtrader/data_feeds
python dukascopy_importer.py
# Select: EURUSD, Date range: Last 7 days
```

**Validation**:
```bash
# Check data loaded
sptrader db query "SELECT count(*) FROM market_data_v2 WHERE symbol='EURUSD'"
sptrader db query "SELECT min(timestamp), max(timestamp) FROM market_data_v2 WHERE symbol='EURUSD'"
```

### 1.2 Create OHLC Aggregates
**Goal**: Generate all timeframe aggregates from tick data

```bash
# Run OHLC manager to create aggregates
cd ~/SPtrader/scripts
python ohlc_manager.py

# Verify OHLC tables populated
sptrader db query "SELECT count(*) FROM ohlc_1m_v2 WHERE symbol='EURUSD'"
sptrader db query "SELECT count(*) FROM ohlc_5m_v2 WHERE symbol='EURUSD'"
sptrader db query "SELECT count(*) FROM ohlc_1h_v2 WHERE symbol='EURUSD'"
```

### 1.3 Create Viewport Tables
**Goal**: Build optimized tables for different zoom levels

```bash
sptrader optimize

# Verify viewport tables
sptrader db query "SELECT table, row_count FROM tables WHERE table LIKE '%viewport%'"
```

## 📈 Phase 2: API Performance Profiling

### 2.1 Response Time Testing
Create test script `~/SPtrader/tools/profile_api.py`:

```python
#!/usr/bin/env python3
"""Profile API performance with different query patterns"""

import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/candles"

def test_query(name, params):
    """Test a single query and return timing"""
    start = time.time()
    response = requests.get(BASE_URL, params=params)
    duration = (time.time() - start) * 1000  # ms
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {name}: {duration:.1f}ms, {len(data)} candles")
        return duration, len(data)
    else:
        print(f"❌ {name}: Failed - {response.status_code}")
        return None, 0

def run_profile():
    """Run various query patterns"""
    end_time = datetime.utcnow()
    
    # Test patterns
    tests = [
        # [name, timeframe, hours_back, expected_candles]
        ("1min - 1 hour", "1m", 1, 60),
        ("1min - 4 hours", "1m", 4, 240),
        ("1min - 24 hours", "1m", 24, 1440),
        ("5min - 1 day", "5m", 24, 288),
        ("5min - 1 week", "5m", 168, 2016),
        ("15min - 1 week", "15m", 168, 672),
        ("1h - 1 month", "1h", 720, 720),
        ("1h - 3 months", "1h", 2160, 2160),
        ("1h - 1 year", "1h", 8760, 8760),
        ("4h - 1 year", "4h", 8760, 2190),
        ("1d - 2 years", "1d", 17520, 730),
    ]
    
    results = []
    print("\n🔍 API Performance Profile")
    print("=" * 60)
    
    for name, tf, hours, expected in tests:
        start = (end_time - timedelta(hours=hours)).isoformat() + 'Z'
        end = end_time.isoformat() + 'Z'
        
        params = {
            "symbol": "EURUSD",
            "tf": tf,
            "start": start,
            "end": end
        }
        
        duration, count = test_query(name, params)
        if duration:
            results.append({
                "test": name,
                "duration_ms": duration,
                "candles": count,
                "candles_per_ms": count / duration if duration > 0 else 0
            })
        
        time.sleep(0.1)  # Don't hammer the API
    
    # Cache warmup test
    print("\n🔥 Cache Warmup Test")
    print("-" * 60)
    
    # Make same request 5 times
    params = {
        "symbol": "EURUSD",
        "tf": "1h",
        "start": (end_time - timedelta(days=30)).isoformat() + 'Z',
        "end": end_time.isoformat() + 'Z'
    }
    
    for i in range(5):
        duration, count = test_query(f"Cache test {i+1}", params)
        time.sleep(0.1)
    
    # Summary
    print("\n📊 Performance Summary")
    print("=" * 60)
    
    if results:
        avg_ms = sum(r["duration_ms"] for r in results) / len(results)
        print(f"Average response time: {avg_ms:.1f}ms")
        
        # Find performance boundaries
        fast = [r for r in results if r["duration_ms"] < 100]
        medium = [r for r in results if 100 <= r["duration_ms"] < 500]
        slow = [r for r in results if r["duration_ms"] >= 500]
        
        print(f"\n⚡ Fast queries (<100ms): {len(fast)}")
        print(f"🔶 Medium queries (100-500ms): {len(medium)}")
        print(f"🐌 Slow queries (>500ms): {len(slow)}")
        
        # Recommendations
        print("\n💡 Recommended Limits:")
        if fast:
            max_fast = max(r["candles"] for r in fast)
            print(f"  - Real-time updates: {max_fast} candles max")
        if medium:
            max_medium = max(r["candles"] for r in medium)
            print(f"  - Normal queries: {max_medium} candles max")
        print(f"  - Consider pagination above 5000 candles")

if __name__ == "__main__":
    run_profile()
```

### 2.2 Viewport Table Performance
Test which tables are used for different zoom levels:

```bash
# Check API stats before and after queries
sptrader api stats

# Make queries that should hit different viewport tables
curl "http://localhost:8000/api/candles?symbol=EURUSD&tf=1h&start=2024-01-01T00:00:00Z&end=2024-12-31T23:59:59Z"
```

## 🔧 Phase 3: Define Data Contracts

### 3.1 API Response Limits
Based on profiling, establish:
```yaml
response_limits:
  real_time_max_candles: 500      # <50ms target
  interactive_max_candles: 2000    # <200ms target  
  background_max_candles: 10000    # <1s target
  
timeframe_defaults:
  1m:
    default_range: "2 hours"
    max_range: "1 day"
  5m:
    default_range: "1 day"
    max_range: "1 week"
  15m:
    default_range: "3 days"
    max_range: "1 month"
  1h:
    default_range: "1 week"
    max_range: "3 months"
  4h:
    default_range: "1 month"
    max_range: "1 year"
  1d:
    default_range: "3 months"
    max_range: "5 years"
```

### 3.2 Viewport Strategy
```yaml
viewport_thresholds:
  detail_view:        # < 500 candles visible
    source: "original_tables"
    sampling: "none"
    
  normal_view:        # 500-2000 candles visible
    source: "1h_viewport"
    sampling: "none"
    
  overview:           # 2000-5000 candles visible
    source: "4h_viewport"
    sampling: "frontend_decimation"
    
  macro_view:         # > 5000 candles visible
    source: "1d_viewport"
    sampling: "aggressive_decimation"
```

## 📱 Phase 4: Chart Behavior Design

### 4.1 Data Loading Strategy
```javascript
// Chart data manager pseudocode
class ChartDataManager {
  constructor() {
    this.viewportWidth = null;
    this.currentTimeframe = '1h';
    this.dataCache = new Map();
    this.pendingRequests = new Map();
  }
  
  async getVisibleData(timeRange) {
    const candles = this.calculateVisibleCandles(timeRange);
    
    if (candles < 500) {
      return this.loadDetailData(timeRange);
    } else if (candles < 2000) {
      return this.loadNormalData(timeRange);
    } else {
      return this.loadAggregatedData(timeRange);
    }
  }
  
  calculateVisibleCandles(timeRange) {
    // Based on timeframe and range
  }
  
  async loadWithPrefetch(centerRange) {
    // Load visible range
    const visible = await this.getVisibleData(centerRange);
    
    // Prefetch left and right
    this.prefetchInBackground(centerRange.expandLeft(0.5));
    this.prefetchInBackground(centerRange.expandRight(0.5));
    
    return visible;
  }
}
```

### 4.2 Interaction Patterns
```yaml
pan_behavior:
  small_pan:          # < 10% of viewport
    action: "use_cache"
    fetch: "none"
    
  medium_pan:         # 10-50% of viewport
    action: "fetch_missing"
    fetch: "incremental"
    
  large_pan:          # > 50% of viewport
    action: "fetch_new_viewport"
    fetch: "full_range"

zoom_behavior:
  zoom_in:
    threshold: "500_candles_visible"
    action: "switch_to_detail_data"
    
  zoom_out:
    threshold: "2000_candles_visible"
    action: "switch_to_viewport_table"
    
timeframe_switch:
  strategy: "clear_and_reload"
  cache: "maintain_time_range"
```

## 🚀 Phase 5: Implementation Order

### 5.1 Backend Optimizations
1. Fix missing `data_source` column issue
2. Ensure viewport tables are properly indexed
3. Add query explain plan endpoint for debugging
4. Implement smart table selection in API

### 5.2 API Enhancements
```python
# Add to main.py
@app.get("/api/candles/explain")
async def explain_query(
    symbol: str, 
    tf: str, 
    start: datetime, 
    end: datetime
):
    """Explain which table will be used and why"""
    
@app.get("/api/candles/limits")
async def get_limits(tf: str):
    """Return recommended limits for timeframe"""
```

### 5.3 Frontend Data Layer
1. Create `DataManager` class
2. Implement caching strategy
3. Add prefetching logic
4. Build loading states

### 5.4 Chart Integration
1. Connect lightweight-charts
2. Implement viewport-aware data loading
3. Add smooth transitions
4. Performance monitoring

## 📊 Phase 6: Testing & Optimization

### 6.1 Load Testing
```bash
# Gradually increase data volume
# Test with multiple symbols
# Measure query degradation
```

### 6.2 Performance Metrics
- Time to first candle
- Time to full viewport
- Pan responsiveness
- Zoom responsiveness
- Cache hit rate
- Memory usage

### 6.3 Optimization Targets
- 90% of queries < 200ms
- Cache hit rate > 70%
- Smooth 60fps panning
- No loading spinners for small pans

## 🎯 Success Criteria

1. **Data Loading**: < 200ms for visible viewport
2. **Interactions**: Smooth panning/zooming at 60fps
3. **Scalability**: Handles 5 years of 1-minute data
4. **User Experience**: No loading states during normal use
5. **Cache Efficiency**: 70%+ hit rate after warmup

---

## Next Steps

1. Run the profiling script
2. Document actual performance numbers
3. Adjust limits based on reality
4. Begin frontend implementation with these constraints