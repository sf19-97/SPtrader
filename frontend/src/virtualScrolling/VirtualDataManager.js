/**
 * VirtualDataManager - Manages candle data for charts
 * 
 * ██╗    ██╗ █████╗ ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
 * ██║    ██║██╔══██╗██╔══██╗████╗  ██║██║████╗  ██║██╔════╝ 
 * ██║ █╗ ██║███████║██████╔╝██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
 * ██║███╗██║██╔══██║██╔══██╗██║╚██╗██║██║██║╚██╗██║██║   ██║
 * ╚███╔███╔╝██║  ██║██║  ██║██║ ╚████║██║██║ ╚████║╚██████╔╝
 *  ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
 *
 * CRITICAL: DO NOT REDUCE WINDOW SIZE OR ENABLE DATA TRIMMING!
 * This class is configured to display ALL historical data. If you trim 
 * older candles or reduce the window size, you will lose historical data!
 * 
 * Any modifications to the applyWindow() or constructor() functions
 * should be carefully reviewed to ensure they don't impact data range.
 *
 * Created: May 30, 2025
 * Last Modified: May 31, 2025 - Fixed historical data display issues
 */

class VirtualDataManager {
  constructor(windowSize = 2000000) { // Increased window size to handle all historical data
    this.windowSize = windowSize;  // Set to a much larger value to ensure we don't lose historical data
    this.window = [];              // Active window of candles
    this.windowStart = null;       // Start timestamp of window
    this.windowEnd = null;         // End timestamp of window
    this.totalDataRange = {        // Track full data availability
      start: null,
      end: null
    };
    this.symbol = null;
    this.timeframe = null;
    this.chart = null;
    this.series = null;
    this.apiBase = 'http://localhost:8080/api/v1';
    
    // Caching
    this.cache = new Map();        // Cache fetched data chunks
    this.maxCacheSize = 10000;     // Max candles to cache
    
    // Loading state
    this.isLoading = false;
    this.loadingDirection = null;  // 'forward' or 'backward'
    
    // Resolution selector for smart timeframe switching
    this.resolutionSelector = typeof ResolutionSelector !== 'undefined' ? new ResolutionSelector() : null;
    this.autoResolution = false;   // Enable automatic resolution switching
  }

  /**
   * Initialize with chart instance and series
   */
  init(chart, series, symbol, timeframe) {
    this.chart = chart;
    this.series = series;
    this.symbol = symbol;
    this.timeframe = timeframe;
    
    // Get available data range
    this.fetchDataRange();
  }

  /**
   * Fetch the total available data range for the symbol
   */
  async fetchDataRange() {
    try {
      const response = await fetch(`${this.apiBase}/data/range?symbol=${this.symbol}`);
      const data = await response.json();
      
      this.totalDataRange = {
        start: new Date(data.start),
        end: new Date(data.end)
      };
      
      console.log(`Data available from ${data.start} to ${data.end}`);
    } catch (error) {
      console.error('Failed to fetch data range:', error);
    }
  }

  /**
   * Update viewport based on visible range
   * This is called when user pans/zooms
   */
  async updateViewport(visibleRange) {
    if (!visibleRange || !visibleRange.from || !visibleRange.to) return;
    
    const visibleStart = new Date(visibleRange.from * 1000);
    const visibleEnd = new Date(visibleRange.to * 1000);
    
    console.log(`Viewport: ${visibleStart.toISOString()} to ${visibleEnd.toISOString()}`);
    
    // Calculate buffer (load extra data outside visible range)
    const visibleDuration = visibleEnd - visibleStart;
    const bufferSize = visibleDuration * 0.5; // 50% buffer on each side
    
    const targetStart = new Date(visibleStart.getTime() - bufferSize);
    const targetEnd = new Date(visibleEnd.getTime() + bufferSize);
    
    // Check if we need to load new data
    const needsUpdate = !this.windowStart || !this.windowEnd ||
                       targetStart < this.windowStart || 
                       targetEnd > this.windowEnd;
    
    if (needsUpdate && !this.isLoading) {
      await this.loadWindowData(targetStart, targetEnd, visibleStart, visibleEnd);
    }
  }

  /**
   * Load data for the window
   */
  async loadWindowData(start, end, visibleStart, visibleEnd) {
    this.isLoading = true;
    
    try {
      // Check cache first
      const cacheKey = `${this.symbol}-${this.timeframe}-${start.toISOString()}-${end.toISOString()}`;
      let candles = this.cache.get(cacheKey);
      
      if (!candles) {
        // Fetch from API
        const params = new URLSearchParams({
          symbol: this.symbol,
          tf: this.timeframe,
          start: start.toISOString(),
          end: end.toISOString()
        });
        
        const response = await fetch(`${this.apiBase}/candles/native/v2?${params}`);
        const data = await response.json();
        candles = data.candles || [];
        
        // Cache the result
        this.addToCache(cacheKey, candles);
      }
      
      // Convert to chart format
      const chartData = candles
        .filter(c => c && c.timestamp)
        .map(candle => ({
          time: new Date(candle.timestamp).getTime() / 1000,
          open: parseFloat(candle.open),
          high: parseFloat(candle.high),
          low: parseFloat(candle.low),
          close: parseFloat(candle.close)
        }))
        .sort((a, b) => a.time - b.time);
      
      // Apply sliding window
      this.applyWindow(chartData, start, end);
      
      // Update series
      this.series.setData(this.window);
      
      console.log(`Loaded ${this.window.length} candles in window`);
      
    } catch (error) {
      console.error('Failed to load window data:', error);
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Apply sliding window to maintain windowSize limit
   * 
   * ⚠️ CRITICAL: THIS FUNCTION MUST NOT TRIM HISTORICAL DATA! ⚠️
   * The original implementation was limiting data to 2000 candles, which
   * caused the loss of historical data before March 2024. The current
   * implementation ensures ALL historical data is preserved.
   * 
   * DO NOT MODIFY THIS FUNCTION without understanding the implications!
   * If you need to improve performance, consider other approaches that
   * don't involve data trimming.
   */
  applyWindow(newData, start, end) {
    // IMPORTANT FIX: Always use the full range of data
    // We want to ensure we don't trim historical data due to window size limitations
    
    // If this is initial load or complete refresh, keep ALL data
    if (!this.windowStart || !this.windowEnd) {
      console.log(`Initial load with ${newData.length} candles`);
      this.window = newData;
      this.windowStart = start;
      this.windowEnd = end;
      return;
    }
    
    // Merge with existing window without trimming
    const merged = this.mergeData(this.window, newData);
    this.window = merged;
    
    // Log data range we're actually displaying
    console.log(`Displaying ${this.window.length} candles from ${start.toISOString()} to ${end.toISOString()}`);
    
    // Update window bounds
    if (this.window.length > 0) {
      this.windowStart = new Date(this.window[0].time * 1000);
      this.windowEnd = new Date(this.window[this.window.length - 1].time * 1000);
    }
  }

  /**
   * Merge two sorted arrays of candle data
   */
  mergeData(existing, newData) {
    const map = new Map();
    
    // Add existing data
    existing.forEach(candle => {
      map.set(candle.time, candle);
    });
    
    // Add/update with new data
    newData.forEach(candle => {
      map.set(candle.time, candle);
    });
    
    // Convert back to sorted array
    return Array.from(map.values()).sort((a, b) => a.time - b.time);
  }

  /**
   * Add data to cache with size limit
   */
  addToCache(key, data) {
    this.cache.set(key, data);
    
    // Enforce cache size limit (simple FIFO)
    if (this.cache.size > 20) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }

  /**
   * Clear all data
   */
  clear() {
    this.window = [];
    this.windowStart = null;
    this.windowEnd = null;
    this.cache.clear();
    
    if (this.series) {
      this.series.setData([]);
    }
  }

  /**
   * Get current window info
   */
  getInfo() {
    return {
      windowSize: this.window.length,
      windowStart: this.windowStart,
      windowEnd: this.windowEnd,
      cacheSize: this.cache.size,
      totalDataRange: this.totalDataRange
    };
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VirtualDataManager;
}