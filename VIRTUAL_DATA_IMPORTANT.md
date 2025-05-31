# ⚠️ CRITICAL: DO NOT MODIFY VIRTUAL DATA MANAGER WITHOUT READING THIS ⚠️

## Historical Data Display Bug Fix

**Date:** May 31, 2025

### The Problem

The charts were only displaying data from March 1, 2024 onwards, despite having data going back to March 1, 2023. This occurred because:

1. The `VirtualDataManager` class had a default window size of only 2,000 candles
2. When loading the full data range (over 277,000 candles), it was only keeping the most recent 2,000
3. This resulted in trimming all older history beyond March 1, 2024

### The Fix

Two key modifications were made:

1. **Increased the window size** from 2,000 to 2,000,000 candles:
   - `/frontend/src/virtualScrolling/VirtualDataManager.js` - constructor
   - `/frontend/renderer.js` - initialization

2. **Modified the `applyWindow` function** to never trim historical data:
   ```javascript
   // Old code (problem):
   if (merged.length > this.windowSize) {
     // Scrolling forward, trim from start
     this.window = merged.slice(-this.windowSize);
   }
   
   // New code (solution):
   // Simply use all data without trimming
   const merged = this.mergeData(this.window, newData);
   this.window = merged;
   ```

### DO NOT REVERT THESE CHANGES

If you:
- Reduce the window size
- Re-enable trimming in the `applyWindow()` function
- Change how `VirtualDataManager` processes historical data

You will reintroduce the bug where historical data (before March 2024) is hidden.

### Performance Considerations

If you need to improve performance:
1. Consider optimizing the rendering rather than reducing data volume
2. Implement data downsampling that preserves the full date range
3. Add pagination controls rather than auto-trimming older data

### Affected Files

1. `/frontend/src/virtualScrolling/VirtualDataManager.js`
2. `/frontend/renderer.js`

Both files have prominent warning comments marking the critical sections.