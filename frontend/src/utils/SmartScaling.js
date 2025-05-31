/**
 * SmartScaling.js
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
        
        this.setupEventHandlers();
    }
    
    /**
     * Set up event handlers for chart interactions
     */
    setupEventHandlers() {
        // Detect when user manually adjusts scale
        this.chart.subscribeClick(param => {
            if (param.point && param.point.y < 40) {
                this.isManualScale = true;
                console.log('Smart scaling: Manual scale mode activated');
            }
        });
        
        // Auto-scale when viewport changes (unless manual)
        this.chart.timeScale().subscribeVisibleTimeRangeChange(() => {
            if (!this.isManualScale) {
                this.autoScaleToVisible();
            }
        });
        
        // Double-click to reset to auto-scale
        this.chart.subscribeDoubleClick(param => {
            if (param.point && param.point.y < 40) {
                this.resetAutoScale();
                console.log('Smart scaling: Auto scale reset');
            }
        });
    }
    
    /**
     * Auto-scales the price axis to show all visible data
     */
    autoScaleToVisible() {
        const timeRange = this.chart.timeScale().getVisibleRange();
        if (!timeRange) return;
        
        // Get data from the series
        const seriesData = this.series.data();
        if (!seriesData || seriesData.length === 0) return;
        
        // Filter to visible data
        const visibleData = seriesData.filter(candle => 
            candle.time >= timeRange.from && candle.time <= timeRange.to
        );
        
        if (visibleData.length === 0) return;
        
        // Find price range
        let minPrice = Infinity;
        let maxPrice = -Infinity;
        
        visibleData.forEach(candle => {
            minPrice = Math.min(minPrice, candle.low);
            maxPrice = Math.max(maxPrice, candle.high);
        });
        
        // Add margins
        const range = maxPrice - minPrice;
        const topMargin = range * this.margins.top;
        const bottomMargin = range * this.margins.bottom;
        
        // Apply custom scale with margins
        this.chart.priceScale('right').applyOptions({
            autoScale: false,
            scaleMargins: {
                top: 0.1,
                bottom: 0.1
            }
        });
        
        // Set the price range with margins
        this.series.priceScale().applyOptions({
            minValue: minPrice - bottomMargin,
            maxValue: maxPrice + topMargin
        });
        
        // Store the current range
        this.lastVisibleRange = {
            minPrice: minPrice - bottomMargin,
            maxPrice: maxPrice + topMargin
        };
    }
    
    /**
     * Resets to automatic scaling
     */
    resetAutoScale() {
        this.isManualScale = false;
        this.chart.priceScale('right').applyOptions({ 
            autoScale: true,
            scaleMargins: {
                top: this.margins.top / 2,
                bottom: this.margins.bottom / 2
            }
        });
    }
    
    /**
     * Lock the price scale to a specific range
     * @param {number} minPrice - Minimum price
     * @param {number} maxPrice - Maximum price
     */
    lockPriceRange(minPrice, maxPrice) {
        this.isManualScale = true;
        this.chart.priceScale('right').applyOptions({
            autoScale: false,
        });
        
        this.series.priceScale().applyOptions({
            minValue: minPrice,
            maxValue: maxPrice
        });
        
        this.lastVisibleRange = {
            minPrice,
            maxPrice
        };
    }
    
    /**
     * Set the margin values for auto-scaling
     * @param {number} top - Top margin (0.0-1.0)
     * @param {number} bottom - Bottom margin (0.0-1.0)
     */
    setMargins(top, bottom) {
        this.margins.top = top;
        this.margins.bottom = bottom;
        
        // Apply to current view if in auto mode
        if (!this.isManualScale) {
            this.autoScaleToVisible();
        }
    }
    
    /**
     * Fit visible content within the price scale
     */
    fitContent() {
        this.chart.priceScale('right').applyOptions({ autoScale: true });
        
        // Briefly allow auto-scaling, then apply our smart scaling
        setTimeout(() => {
            this.autoScaleToVisible();
        }, 50);
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