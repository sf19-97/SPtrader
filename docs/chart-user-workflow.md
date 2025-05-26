# Chart User Workflow - Frontend to Backend

## 🖱️ User Actions → Backend Processing

```mermaid
graph TD
    subgraph "👤 User Actions"
        A1[Open Chart Page]
        A2[Scroll Left/Right]
        A3[Zoom In/Out]
        A4[Change Timeframe]
        A5[View Real-time Updates]
    end

    subgraph "🌐 Frontend Processing"
        B1[Detect Viewport Change]
        B2[Calculate Time Range]
        B3[Check Browser Cache]
        B4[Determine Resolution]
        B5[Make API Request]
    end

    subgraph "⚡ Gin Backend"
        C1[Parse Request]
        C2[Select Optimal Table]
        C3[Check Redis Cache]
        C4[Query QuestDB]
        C5[Stream Updates]
    end

    subgraph "💾 Data Layer"
        D1[ohlc_5m table]
        D2[ohlc_1h_viewport]
        D3[ohlc_4h_viewport]
        D4[ohlc_1d_viewport]
        D5[Real-time Feed]
    end

    A1 -->|Initial Load| B1
    A2 -->|Pan Event| B1
    A3 -->|Zoom Event| B1
    A4 -->|Dropdown Change| B1
    A5 -->|WebSocket| C5

    B1 --> B2
    B2 --> B3
    B3 -->|Cache Miss| B4
    B3 -->|Cache Hit| E1[Display Data]
    B4 --> B5
    B5 --> C1

    C1 --> C2
    C2 --> C3
    C3 -->|Redis Hit| E1
    C3 -->|Redis Miss| C4
    
    C2 -->|5m-24h| D1
    C2 -->|1h-7d| D2
    C2 -->|4h-30d| D3
    C2 -->|1d-1y| D4
    
    C4 --> E1
    C5 --> D5
    D5 --> E2[Update Chart]
```

## 📋 Detailed User Scenarios

### 1. **Initial Chart Load**
```
User Opens EUR/USD Chart
↓
Frontend: "What's visible?" → Last 24 hours
↓
Check Browser Cache → Empty
↓
API Call: GET /api/candles?symbol=EURUSD&start=2024-01-24&end=2024-01-25
↓
Backend: "24 hour range → Use 5m resolution from ohlc_5m table"
↓
Query: SELECT * FROM ohlc_5m WHERE... (288 candles)
↓
Return Data + Cache Headers
↓
Frontend: Cache response + Draw chart
```

### 2. **User Scrolls Left (Historical Data)**
```
User Scrolls Left on Chart
↓
Frontend: Detect mouse wheel deltaX < 0
↓
Calculate: Need previous 24 hours
↓
Check Browser Cache → Not found
↓
API: GET /api/candles?symbol=EURUSD&start=2024-01-23&end=2024-01-24
↓
Backend: Still 24h range → Still 5m data
↓
Return 288 more candles
↓
Frontend: Prepend to chart + Smooth animation
```

### 3. **User Zooms Out (Week View)**
```
User: Scroll wheel zoom out
↓
Frontend: Viewport now shows 7 days
↓
Calculate: Too many 5m candles (2016 points)
↓
API: GET /api/candles?symbol=EURUSD&start=2024-01-18&end=2024-01-25
↓
Backend: "7 day range → Switch to 1h resolution"
↓
Query: SELECT * FROM ohlc_1h_viewport WHERE... (168 candles)
↓
Frontend: Replace chart with hourly candles
```

### 4. **User Zooms Way Out (Year View)**
```
User: Zoom to 1 year view
↓
Frontend: Viewport = 365 days
↓
API: GET /api/candles?symbol=EURUSD&start=2023-01-25&end=2024-01-25
↓
Backend Logic:
  if (range > 30 days) {
    table = "ohlc_1d_viewport"  // Daily candles
    resolution = "1D"
  }
↓
Query: Returns 365 daily candles
↓
Frontend: Smooth transition to daily view
```

### 5. **Real-time Updates (Live Trading)**
```
User: Viewing current day
↓
Frontend: Opens WebSocket connection
↓
WS: ws://localhost:8080/api/ws?symbol=EURUSD
↓
Backend: Subscribe to Oanda feed
↓
Every tick:
  - Update current candle
  - Broadcast to WebSocket
↓
Frontend: Update last candle without redraw
```

## 🔄 Performance Optimizations

### **Browser Cache Flow**
```
1. First Request → Store in Cache API
2. Second Request → Instant load (0ms)
3. Background → Prefetch adjacent periods
4. Result → Pan/scroll feels instant
```

### **Backend Decision Tree**
```go
func (h *Handler) selectOptimalTable(start, end time.Time) string {
    duration := end.Sub(start)
    
    switch {
    case duration <= 24*time.Hour:
        return "ohlc_5m"        // 288 points max
    case duration <= 7*24*time.Hour:
        return "ohlc_1h_viewport"   // 168 points max
    case duration <= 30*24*time.Hour:
        return "ohlc_4h_viewport"   // 180 points max
    default:
        return "ohlc_1d_viewport"   // 365 points max
    }
}
```

## 📊 Data Volume Examples

| User View | Time Range | Resolution | Data Points | Query Time |
|-----------|------------|------------|-------------|------------|
| Intraday | 24 hours | 5-minute | 288 | ~10ms |
| Week | 7 days | 1-hour | 168 | ~15ms |
| Month | 30 days | 4-hour | 180 | ~20ms |
| Year | 365 days | Daily | 365 | ~25ms |

## 🚀 User Experience Results

- **Initial Load**: < 100ms (feels instant)
- **Pan/Scroll**: < 50ms (with prefetch)
- **Zoom**: < 200ms (resolution change)
- **Memory Used**: ~5MB per chart
- **Cache Hit Rate**: 80%+ after first minute

The key insight: Users think they're viewing "all the data" but they're actually only seeing 200-400 optimally chosen data points at any time!