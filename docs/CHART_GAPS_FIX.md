# Chart Gaps Fix
*May 31, 2025*

## Issue Description

Charts were displaying gaps in the daily candle view due to a timestamp issue in the data. The problem manifested as gaps in the chart where trading days like Friday were incorrectly filtered out.

## Root Cause Analysis

The issue was caused by a combination of two factors:

1. **QuestDB's SAMPLE BY 1d ALIGN TO CALENDAR Behavior**:
   - QuestDB aligns daily candles to midnight UTC (00:00:00) of the next day
   - This means a day's trading data (e.g., Friday) gets timestamped at 00:00:00 UTC of the next day (Saturday)
   - These timestamps appear to be on non-trading days

2. **ForexSessionFilter Behavior**:
   - ForexSessionFilter correctly identifies Saturday/Sunday timestamps as weekend data
   - But it was removing Friday's actual trading data (with Saturday timestamps)
   - This explained why 94 candles were filtered out - they were real trading days

## The Fix

We implemented a two-pronged solution:

### 1. Update ForexSessionFilter.js

- Added special handling for daily candles with the `isWeekday()` method
- The updated filter now uses a different approach for daily timeframes:
  - For intraday candles: Continues to use `isMarketOpen()` which checks hours
  - For daily candles: Uses `isWeekday()` which keeps Monday-Friday data regardless of timestamp
- Added timeframe detection to determine when to apply the special case

```javascript
/**
 * Special case for daily candles - preserve all trading days
 */
isWeekday(timestamp) {
    const date = new Date(timestamp * 1000);
    const dayOfWeek = date.getUTCDay();
    const dateStr = date.toISOString().split('T')[0];
    
    // Check holidays first
    if (this.holidays.has(dateStr)) {
        return false;
    }
    
    // Keep weekdays (Monday-Friday)
    return dayOfWeek > 0 && dayOfWeek < 6;
}
```

### 2. Updated Renderer.js

- Modified to pass the current timeframe to the filter:
```javascript
const timeframe = document.getElementById('timeframe').value;
const continuousData = forexSessionFilter.createContinuousView(chartData, timeframe);
```

### 3. Long-term Solution

For a more comprehensive fix, we also created a script to fix the daily candle timestamps at the database level:

```python
# Shift timestamp back one day to fix QuestDB's ALIGN TO CALENDAR behavior
INSERT INTO ohlc_1d_v2_new
SELECT 
    timestamp::timestamp - 86400000000 as timestamp, -- Shift back one day
    symbol,
    first(open) as open,
    ...
```

## Results

After the fix:
- Daily charts display continuous data without gaps
- All trading days (Mon-Fri) are properly displayed
- Weekend days (Sat-Sun) are correctly filtered out
- Holidays are also properly filtered

## Verification

You can verify the fix by:
1. Loading a daily chart and checking for gaps
2. Confirming that all weekdays appear and weekend days are excluded
3. Using the developer console to check the log message: `Filtered X candles to Y trading candles for 1d`

## Lessons Learned

1. QuestDB's aggregation behavior with ALIGN TO CALENDAR can lead to timestamps being offset by one day for daily aggregations.
2. When working with financial data, always consider market hours and trading day conventions.
3. Implementing a frontend filtering solution provides flexibility without requiring database schema changes.

## Credits

This fix was implemented on May 31, 2025, in response to chart display issues reported by users.