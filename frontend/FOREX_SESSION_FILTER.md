# Forex Session Filter for Continuous Charts
*Last Updated: May 31, 2025 - 22:30 UTC*

## Overview

The Forex Session Filter is a specialized component that handles the unique trading schedule of the forex market. Unlike stock markets that simply close on weekends, forex markets have a weekly schedule (Sunday 22:00 UTC to Friday 22:00 UTC) with various holidays.

This utility creates continuous-looking charts by:
1. Filtering out non-trading periods (weekends, holidays)
2. Creating a continuous timeline for the remaining trading periods
3. Correctly handling the transitions between trading sessions

## How It Works

### 1. Market Hours Definition

Forex markets follow this general schedule:
- **Open**: Sunday 22:00 UTC (10 PM)
- **Close**: Friday 22:00 UTC (10 PM)
- **Weekend**: Friday 22:00 UTC to Sunday 22:00 UTC
- **Holidays**: Various global banking holidays

### 2. Key Features

- **Trading Period Detection**: Automatically identifies when markets are open
- **Holiday Calendar**: Built-in calendar for 2023-2025 holidays
- **Continuous Timeline**: Eliminates gaps between trading sessions
- **Interval Detection**: Automatically detects the candle timeframe
- **Original Time Preservation**: Keeps original timestamps for reference

### 3. Integration with Chart

The filter integrates with the chart display process:
1. Raw data is fetched from the API
2. Filter processes the data to create a continuous view
3. Chart displays the processed data without gaps
4. Technical analysis works correctly without weekend distortions

## Usage

### Basic Usage
```javascript
// Create filter instance
const forexSessionFilter = new ForexSessionFilter();

// Get continuous data
const continuousData = forexSessionFilter.createContinuousView(rawCandles);

// Set chart data
candleSeries.setData(continuousData);
```

### Adding Custom Holidays
```javascript
// Add specific holidays
forexSessionFilter.addHoliday('2025-12-24'); // Christmas Eve
```

## Files

1. `/frontend/src/utils/forex_session_filter.js` - Main implementation
2. `/frontend/renderer.js` - Integration with chart display
3. `/frontend/preload.js` - Module loading support
4. `/frontend/index.html` - Script initialization
5. `/frontend/src/utils/test_filter.js` - Unit test for filter
6. `/scripts/fix_electron_sandbox.sh` - Sandbox permissions fixer

## Benefits

- **Smoother Charts**: No visual breaks during weekends/holidays
- **Better Analysis**: Technical indicators work properly without distortion
- **TradingView-Like**: Mimics professional trading platforms
- **Better UX**: No confusing jumps in the timeline

## Installation Notes

The code has been integrated and the Electron permissions have been successfully fixed. The application should now run without issues:

```bash
# Run the desktop app
cd frontend && npm run start
```

If you need to fix sandbox permissions again (after npm install or on a new system):
```bash
# Run the sandbox fix script from the SPtrader root directory
scripts/fix_electron_sandbox.sh
```

Alternatively, you can run without sandbox:
```bash
cd frontend && npm run start -- --no-sandbox
```

For more details, see [ELECTRON_SANDBOX_FIX.md](./ELECTRON_SANDBOX_FIX.md)

## Testing

The forex session filter has been tested and confirmed working correctly:

```bash
# Run unit test
cd frontend/src/utils && node test_filter.js
```

Test results show that:
- The filter correctly identifies market open/closed periods
- Holiday detection works properly (e.g., Whit Monday 2025-05-26)
- Continuous view generation removes gaps correctly

## Implementation Details

This implementation was inspired by TradingView's approach to forex charts. The key difference between our approach and other solutions:

1. **Two-Step Process**: First filter out non-trading periods, then create a continuous timeline
2. **Automatic Interval Detection**: Works with any timeframe from 1m to 1d
3. **Efficient Algorithm**: Uses a sliding window to maintain O(n) performance
4. **Original Time Reference**: Keeps the original timestamps for data export

## Code Examples

### Checking If Market Is Open
```javascript
isMarketOpen(timestamp) {
    const date = new Date(timestamp * 1000);
    const dayOfWeek = date.getUTCDay();
    const hour = date.getUTCHours();
    const dateStr = date.toISOString().split('T')[0];
    
    // Check holidays first
    if (this.holidays.has(dateStr)) {
        return false;
    }
    
    // Check regular market hours
    if (dayOfWeek === 0) { // Sunday
        return hour >= this.marketOpen.hour;
    } else if (dayOfWeek === 6) { // Saturday
        return false;
    } else if (dayOfWeek === 5) { // Friday
        return hour < this.marketClose.hour;
    } else { // Monday-Thursday
        return true;
    }
}
```

### Creating Continuous Timeline
```javascript
createContinuousView(candles) {
    // First filter out non-trading periods
    const filtered = this.filterCandles(candles);
    
    // Detect the interval between candles
    const interval = this.detectInterval(filtered);
    
    // Create continuous timeline
    const continuous = [];
    let expectedTime = filtered[0].time;
    
    for (let i = 0; i < filtered.length; i++) {
        const candle = { ...filtered[i] };
        
        // Save original time for reference
        candle.originalTime = candle.time;
        
        // Set the continuous time
        candle.time = expectedTime;
        
        // Update expected time for next candle
        expectedTime += interval;
        
        continuous.push(candle);
    }
    
    return continuous;
}
```