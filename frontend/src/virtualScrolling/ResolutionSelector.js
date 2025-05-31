/**
 * ResolutionSelector - Automatically selects optimal timeframe based on zoom level
 * Phase 2 of Virtual Scrolling Implementation
 * Created: May 30, 2025
 */

class ResolutionSelector {
  constructor() {
    // Resolution rules based on visible time range
    this.resolutionRules = [
      { maxHours: 24, resolution: '1m' },        // < 1 day: 1-minute
      { maxHours: 168, resolution: '5m' },       // < 7 days: 5-minute  
      { maxHours: 720, resolution: '15m' },      // < 30 days: 15-minute
      { maxHours: 2160, resolution: '1h' },      // < 90 days: 1-hour
      { maxHours: 8760, resolution: '4h' },      // < 1 year: 4-hour
      { maxHours: Infinity, resolution: '1d' }   // > 1 year: daily
    ];
    
    this.currentResolution = null;
    this.onResolutionChange = null; // Callback when resolution changes
  }

  /**
   * Get optimal resolution for a given time range
   */
  getOptimalResolution(visibleRange) {
    if (!visibleRange || !visibleRange.from || !visibleRange.to) {
      return '1h'; // Default
    }
    
    // Calculate visible hours
    const visibleMs = (visibleRange.to - visibleRange.from) * 1000;
    const visibleHours = visibleMs / (1000 * 60 * 60);
    
    // Find appropriate resolution
    for (const rule of this.resolutionRules) {
      if (visibleHours <= rule.maxHours) {
        return rule.resolution;
      }
    }
    
    return '1d'; // Fallback
  }

  /**
   * Check if resolution should change based on new range
   */
  checkResolution(visibleRange) {
    const optimalResolution = this.getOptimalResolution(visibleRange);
    
    if (optimalResolution !== this.currentResolution) {
      const oldResolution = this.currentResolution;
      this.currentResolution = optimalResolution;
      
      console.log(`Resolution change: ${oldResolution} → ${optimalResolution}`);
      
      // Trigger callback if set
      if (this.onResolutionChange) {
        this.onResolutionChange(optimalResolution, oldResolution);
      }
      
      return true; // Resolution changed
    }
    
    return false; // No change
  }

  /**
   * Get info about current state
   */
  getInfo(visibleRange) {
    if (!visibleRange || !visibleRange.from || !visibleRange.to) {
      return {
        visibleHours: 0,
        optimalResolution: this.currentResolution || '1h',
        candleEstimate: 0
      };
    }
    
    const visibleMs = (visibleRange.to - visibleRange.from) * 1000;
    const visibleHours = visibleMs / (1000 * 60 * 60);
    const optimalResolution = this.getOptimalResolution(visibleRange);
    
    // Estimate number of candles
    let candlesPerHour;
    switch (optimalResolution) {
      case '1m': candlesPerHour = 60; break;
      case '5m': candlesPerHour = 12; break;
      case '15m': candlesPerHour = 4; break;
      case '30m': candlesPerHour = 2; break;
      case '1h': candlesPerHour = 1; break;
      case '4h': candlesPerHour = 0.25; break;
      case '1d': candlesPerHour = 0.0417; break; // ~1/24
      default: candlesPerHour = 1;
    }
    
    const candleEstimate = Math.ceil(visibleHours * candlesPerHour);
    
    return {
      visibleHours: Math.round(visibleHours),
      optimalResolution,
      candleEstimate
    };
  }

  /**
   * Set callback for resolution changes
   */
  setOnResolutionChange(callback) {
    this.onResolutionChange = callback;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ResolutionSelector;
}