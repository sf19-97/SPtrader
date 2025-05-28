# Virtual Scrolling Implementation Plan
*Created: May 27, 2025 13:05 UTC*

## Goal
Create TradingView-like smooth infinite scrolling with constant performance regardless of data size.

## Phase 1: Basic Virtual Scrolling
**Objective**: Only render visible candles

### Frontend Changes
```javascript
// New VirtualDataManager class
class VirtualDataManager {
  constructor(windowSize = 2000) {
    this.window = [];          // Active window of candles
    this.windowSize = windowSize;
    this.totalDataRange = {};  // Track full data availability
  }
  
  async updateViewport(visibleRange) {
    // Determine what data we need
    // Maintain window around visible area
    // Fetch missing data from API
  }
}
```

### API Changes Needed
- None initially - current endpoints work

### Benefits
- Chart only handles 2000 candles max
- Smooth scrolling even with years of data
- Predictable memory usage

## Phase 2: Smart Resolution Switching
**Objective**: Show appropriate detail for zoom level

### Logic
- Zoomed in (< 1 day): 1-minute candles
- Medium (1-7 days): 5-minute candles  
- Zoomed out (> 7 days): 1-hour candles
- Very zoomed out (> 30 days): Daily candles

### API Enhancement
```go
// Add resolution hint endpoint
GET /api/v1/candles/optimal?symbol=EURUSD&from=X&to=Y
Returns: { 
  "recommendedTf": "5m",
  "candleCount": 1440 
}
```

## Phase 3: Predictive Loading
**Objective**: Load data before user needs it

### Features
- Detect scroll velocity and direction
- Pre-load in scroll direction
- Aggressive caching of nearby data
- Background fetching

## Phase 4: Advanced Optimizations

### 1. Binary Data Format
- Replace JSON with MessagePack or Protobuf
- 50-70% smaller payloads
- Faster parsing

### 2. WebSocket Streaming
```javascript
// Stream candles as user scrolls
ws.send({ 
  action: 'subscribe',
  range: { from: X, to: Y },
  resolution: 'auto'
});
```

### 3. Delta Updates
- Only send changed candles
- Efficient for real-time updates
- Reduces bandwidth

## Implementation Order

### Step 1: Basic Window (2-3 hours)
1. Create VirtualDataManager class
2. Implement sliding window logic
3. Hook into existing viewport change events
4. Test with large datasets

### Step 2: Resolution Switching (2 hours)
1. Add zoom level detection
2. Implement resolution selection logic
3. Clear/reload on resolution change
4. Smooth transitions

### Step 3: Predictive Loading (2 hours)
1. Add scroll velocity tracking
2. Implement predictive fetch logic
3. Background data fetching
4. Smart cache management

### Step 4: Performance Monitoring
1. Add metrics collection
2. Monitor frame rates
3. Track data fetch times
4. Optimize based on metrics

## Success Metrics
- Maintain 60 FPS while scrolling
- < 50ms data fetch times
- Support 10+ years of minute data
- < 100MB memory usage
- Instant scrolling response

## Code Structure
```
frontend/
  src/
    virtualScrolling/
      VirtualDataManager.js
      ResolutionSelector.js
      PredictiveLoader.js
      PerformanceMonitor.js
```

## Testing Plan
1. Load 5 years of minute data
2. Rapid scrolling tests
3. Zoom in/out stress test
4. Memory profiling
5. Network failure handling