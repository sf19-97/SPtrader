/**
 * SmartScaling.js - Simplified Version
 * Advanced price scaling management for LightweightCharts
 * Created: May 31, 2025
 */

class SmartScaling {
    /**
     * Creates a SmartScaling instance to manage chart scaling
     * @param {IChartApi} chart - LightweightCharts chart instance
     * @param {ISeriesApi} series - Chart series (usually candlestick series)
     */
    constructor(chart, series) {
        this.chart = chart;
        this.series = series;
        this.isManualScale = false;
        this.lastVisibleRange = null;
        this.margins = {
            top: 0.2,    // 20% margin at top for forex volatility
            bottom: 0.1  // 10% margin at bottom
        };
        console.log('SmartScaling initialized!');
    }
    
    /**
     * Apply optimized scaling margins for forex
     */
    applyForexMargins() {
        // Apply ideal margins for forex
        this.chart.priceScale('right').applyOptions({
            scaleMargins: {
                top: this.margins.top,     // 20% margin at top
                bottom: this.margins.bottom // 10% margin at bottom
            }
        });
        console.log('Applied forex-optimized margins');
    }
    
    /**
     * Enable auto-scaling with proper margins
     */
    enableAutoScale() {
        this.isManualScale = false;
        this.chart.priceScale('right').applyOptions({ 
            autoScale: true,
            scaleMargins: {
                top: this.margins.top,
                bottom: this.margins.bottom
            }
        });
        console.log('Auto-scaling enabled with forex margins');
    }
    
    /**
     * Disable auto-scaling (manual mode)
     */
    disableAutoScale() {
        this.isManualScale = true;
        this.chart.priceScale('right').applyOptions({
            autoScale: false
        });
        console.log('Auto-scaling disabled (manual mode)');
    }
    
    /**
     * Toggle auto-scaling on/off
     */
    toggleAutoScale() {
        const isAuto = this.chart.priceScale('right').options().autoScale;
        if (isAuto) {
            this.disableAutoScale();
            return false;
        } else {
            this.enableAutoScale();
            return true;
        }
    }
    
    /**
     * Set the margin values for auto-scaling
     * @param {number} top - Top margin (0.0-1.0)
     * @param {number} bottom - Bottom margin (0.0-1.0)
     */
    setMargins(top, bottom) {
        this.margins.top = top;
        this.margins.bottom = bottom;
        this.applyForexMargins();
    }
    
    /**
     * Fit visible content within the price scale
     */
    fitContent() {
        // Enable auto-scale with proper margins
        this.enableAutoScale();
        console.log('Fitting content with optimized margins');
    }
}

// For module imports
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmartScaling;
} 
// For browser/script tag usage
else if (typeof window !== 'undefined') {
    window.SmartScaling = SmartScaling;
}