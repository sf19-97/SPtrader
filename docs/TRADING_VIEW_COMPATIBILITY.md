# TradingView-Compatible Forex Display
*May 31, 2025*

## Overview

This document describes the implementation of TradingView-compatible forex chart display in SPtrader. The changes ensure that all timeframes render with the same visual continuity as TradingView charts, particularly around weekend transitions.

## Forex Market Hours

Forex markets operate on the following schedule:
- **Open**: Sunday 22:00 UTC
- **Close**: Friday 22:00 UTC
- **Weekend**: Friday 22:00 UTC to Sunday 22:00 UTC (markets closed)

## Challenges Addressed

### 1. Weekend Display

Traditional time-series charts would show gaps during weekend closures. However, TradingView presents a continuous visual timeline by:

- Preserving exact trading times (hh:mm)
- Connecting the last Friday candle directly to the first Sunday candle
- Eliminating visual gaps while maintaining time precision

### 2. Daily Candle Timestamps

We fixed two types of timestamp issues in daily candles:
- Friday data incorrectly timestamped on Saturday (database issue)
- Legitimate Sunday market open data (correctly preserved)

## Implementation Details

### 1. ForexSessionFilter

The `ForexSessionFilter` class has been enhanced to match TradingView's behavior exactly:

```javascript
// Handle weekend jumps like TradingView
if (lastTradingDay === 5 && candleDay === 0) {
    // Jump from Friday to Sunday (maintain exact times)
    // This skips Saturday completely while maintaining a continuous series
    expectedTime = candle.time - interval;
}
```

This implementation:
- Detects jumps from Friday (day 5) to Sunday (day 0)
- Adjusts the continuous timeline without changing actual timestamps
- Connects the Friday close directly to Sunday open

### 2. Database Timestamp Fix

We implemented a database-level fix for incorrect weekend timestamps:
- Created `fix_weekend_timestamps.py` to identify and correct timestamps
- Preserved legitimate Sunday market open candles
- Shifted incorrect Saturday timestamps (Friday data) back by one day

The script intelligently differentiates between:
- Legitimate weekend data (Sunday market open, ~12% of candles)
- Shifted weekday data (Friday data with Saturday timestamp)

## Timeframe-Specific Behavior

All timeframes now display with TradingView-compatible continuity:

| Timeframe | Behavior |
|-----------|----------|
| 5m, 15m, 30m | Continuous display with exact trading times preserved |
| 1h | Connects Friday evening directly to Sunday evening |
| 4h | Seamless weekend transition with preserved trading hours |
| 1d | Special handling with weekday-only display |

## Verification

You can verify the fix by:
1. Loading charts in different timeframes
2. Checking the weekend transition (Friday to Sunday)
3. Comparing with TradingView's display of the same instruments

## References

- [QuestDB Documentation](https://questdb.io/docs/) - For timestamp handling
- [ForexSessionFilter.js](../frontend/src/utils/forex_session_filter.js) - Implementation details
- [CHART_GAPS_FIX_UPDATE.md](../CHART_GAPS_FIX_UPDATE.md) - Database-level fixes