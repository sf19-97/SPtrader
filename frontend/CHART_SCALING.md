# Chart Scaling Improvements in SPtrader
*Last Updated: May 31, 2025*

## Overview

This document explains the auto-scaling improvements made to the SPtrader chart system. The new implementation uses the `SmartScaling` class to provide better handling of price scales in forex charts, similar to TradingView's professional behavior.

## Problem Solved

Previously, the chart had issues with price scaling:

1. Auto-scaling was disabled by default, causing:
   - New data would appear squished or cut off
   - Charts required manual rescaling frequently
   - Poor user experience when scrolling

2. The temporary fix used was:
   ```javascript
   // Briefly enable auto-scale, then disable it again
   chart.priceScale('right').applyOptions({ autoScale: true });
   chart.timeScale().fitContent();
   setTimeout(() => {
     chart.priceScale('right').applyOptions({ autoScale: false });
   }, 100);
   ```

This approach had several issues:
- Scale would only adjust when loading data or clicking "Fit"
- Price range would stay fixed when scrolling
- Manual scaling was difficult and imprecise

## Solution: SmartScaling Class

The new `SmartScaling` class implements TradingView-like scaling behavior:

### Key Features

1. **Intelligent Auto-Scaling**
   - Automatically scales to show all visible candles
   - Adds appropriate margins for forex volatility
   - Maintains stability when scrolling/zooming

2. **Manual Override Detection**
   - Detects when user manually adjusts price scale
   - Switches to manual mode automatically
   - Double-click to reset to auto-scaling

3. **Viewport-Aware Scaling**
   - Only scales based on visible data
   - Adjusts dynamically as user scrolls
   - Prevents "jumping" when loading new data

4. **Optimized for Forex**
   - 20% top margin for volatility spikes
   - 10% bottom margin for price drops
   - 5-decimal precision for forex pairs

## Implementation Details

### Files Changed

1. **New Files:**
   - `/frontend/src/utils/SmartScaling.js` - Main implementation
   - `/frontend/test_smart_scaling.html` - Test page

2. **Modified Files:**
   - `/frontend/index.html` - Added script reference
   - `/frontend/renderer.js` - Integrated SmartScaling

### Key Code Changes

1. **Chart Configuration:**
   ```javascript
   rightPriceScale: {
     borderColor: '#3a3a3a',
     scaleMargins: {
       top: 0.2,    // More space at top for volatility
       bottom: 0.1, // Less space at bottom
     },
     mode: 0,       // Normal mode (not percentage)
     autoScale: true, // Enable auto-scaling by default
   }
   ```

2. **SmartScaling Integration:**
   ```javascript
   // Create and initialize SmartScaling instance
   smartScaling = new SmartScaling(chart, candleSeries);
   
   // Use for fitting content
   smartScaling.fitContent();
   ```

3. **Fit Button Improvements:**
   ```javascript
   document.getElementById('fit-chart').addEventListener('click', () => {
     // Use SmartScaling to fit content properly
     smartScaling.fitContent();
     chart.timeScale().fitContent();
   });
   ```

## Testing

A test page has been created to verify the behavior:

```
/frontend/test_smart_scaling.html
```

You can test the following:
1. Load simulated forex data
2. Compare auto-scale ON vs OFF behavior
3. Test zooming and scrolling with both modes
4. Verify the "Fit Chart" button works correctly

## Benefits

- **Better UX:** Charts always show appropriate price range
- **TradingView-Like:** Professional chart behavior
- **Reduced Manual Scaling:** Less user intervention needed
- **Smoother Experience:** No jarring jumps when loading data
- **Forex Optimized:** Proper margins for currency volatility

## How to Use

The integration is automatic. The behavior will be:

1. By default, charts auto-scale to show all visible data
2. When a user manually adjusts the price scale, it switches to manual mode
3. The "Fit Chart" button (⊡) will reset to auto-scaling mode
4. Double-clicking on the price scale also resets to auto-scaling

## Recommended Settings for Forex Charts

```javascript
// Optimal auto-scaling for forex charts
rightPriceScale: {
  mode: 0,  // Normal price mode
  autoScale: true,  // Enable auto-scaling
  invertScale: false,
  alignLabels: true,
  borderVisible: true,
  borderColor: '#2a2a2a',
  scaleMargins: {
    top: 0.2,    // 20% margin for forex volatility
    bottom: 0.1, // 10% margin at bottom
  },
}

// For the series
candleSeries = chart.addCandlestickSeries({
  priceFormat: {
    type: 'price',
    precision: 5,     // 5 decimals for forex
    minMove: 0.00001, // Minimum price movement
  },
});
```