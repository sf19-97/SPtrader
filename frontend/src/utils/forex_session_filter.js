/**
 * Forex Session Filter
 * 
 * Handles non-trading periods in forex markets for chart display.
 * Creates continuous-looking charts by removing weekends and holidays.
 * 
 * Created: May 31, 2025
 * Updated: May 31, 2025 - Added special handling for daily candles and Sunday market open
 */

class ForexSessionFilter {
    constructor() {
        // Forex market hours: Sunday 22:00 UTC - Friday 22:00 UTC
        this.marketOpen = { day: 0, hour: 22 }; // Sunday 10 PM
        this.marketClose = { day: 5, hour: 22 }; // Friday 10 PM
        
        // Known forex holidays for 2023-2025
        this.holidays = new Set([
            // 2023 Holidays
            '2023-01-01', // New Year's Day
            '2023-04-07', // Good Friday
            '2023-04-10', // Easter Monday
            '2023-05-29', // Spring Bank Holiday
            '2023-12-25', // Christmas
            '2023-12-26', // Boxing Day
            
            // 2024 Holidays
            '2024-01-01', // New Year's Day
            '2024-03-29', // Good Friday
            '2024-04-01', // Easter Monday
            '2024-05-27', // Spring Bank Holiday
            '2024-12-25', // Christmas
            '2024-12-26', // Boxing Day
            
            // 2025 Holidays
            '2025-01-01', // New Year's Day
            '2025-04-18', // Good Friday
            '2025-04-21', // Easter Monday
            '2025-05-26', // Whit Monday/Spring Bank Holiday
            '2025-12-25', // Christmas
            '2025-12-26', // Boxing Day
        ]);

        // Keep track of candles we've processed for debugging
        this.processedCandles = {
            total: 0,
            filtered: 0
        };
    }
    
    /**
     * Check if the market is open at a given timestamp
     * @param {number} timestamp - Unix timestamp (seconds)
     * @returns {boolean} - True if market is open
     */
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
    
    /**
     * Special case for daily candles - preserve all trading days
     * This method preserves Monday-Friday candles regardless of timestamp
     * Also keeps Sunday candles when they represent the market open period
     * @param {number} timestamp - Unix timestamp (seconds)
     * @returns {boolean} - True if it's a trading day
     */
    isWeekday(timestamp) {
        const date = new Date(timestamp * 1000);
        const dayOfWeek = date.getUTCDay();
        const hour = date.getUTCHours();
        const dateStr = date.toISOString().split('T')[0];
        
        // Check holidays first
        if (this.holidays.has(dateStr)) {
            return false;
        }
        
        // Special case: Sunday with market open time
        // Forex market opens on Sunday evening (~22:00 UTC)
        if (dayOfWeek === 0 && hour >= this.marketOpen.hour) {
            return true;
        }
        
        // Keep weekdays (Monday-Friday)
        return dayOfWeek > 0 && dayOfWeek < 6;
    }
    
    /**
     * Filter out candles during non-trading periods
     * @param {Array} candles - Array of candle objects with time property
     * @param {boolean} isDaily - Whether these are daily candles
     * @returns {Array} - Filtered candles
     */
    filterCandles(candles, isDaily = false) {
        this.processedCandles.total = candles.length;
        
        // For daily candles, use weekday filter
        // For intraday candles, use market hours filter
        const filteredCandles = candles.filter(candle => 
            isDaily ? this.isWeekday(candle.time) : this.isMarketOpen(candle.time)
        );
        
        this.processedCandles.filtered = candles.length - filteredCandles.length;
        console.log(`Filtered ${this.processedCandles.filtered} candles out of ${this.processedCandles.total}`);
        
        return filteredCandles;
    }
    
    /**
     * Create a continuous view by eliminating gaps in the time series
     * Matches TradingView's behavior for forex charts
     * @param {Array} candles - Array of candle objects
     * @param {string} timeframe - Timeframe code (1m, 5m, ..., 1d)
     * @returns {Array} - Continuous candles with adjusted timestamps
     */
    createContinuousView(candles, timeframe = null) {
        if (!candles || candles.length === 0) {
            return [];
        }
        
        // Determine if these are daily candles
        const isDaily = timeframe === '1d' || this.guessTimeframe(this.detectInterval(candles)) === '1d';
        
        // Reset counters
        this.processedCandles = {
            total: 0,
            filtered: 0
        };
        
        // Filter out non-trading periods
        const filtered = this.filterCandles(candles, isDaily);
        if (filtered.length === 0) {
            return [];
        }
        
        // Detect the interval between candles
        const interval = this.detectInterval(filtered);
        
        // Create TradingView-style continuous timeline
        const continuous = [];
        
        // For hours/minutes timeframes, use true continuous view with exact TradingView behavior
        if (!isDaily && timeframe !== '1d' && interval < 86400) { // Less than daily timeframes
            let lastTradingDay = null;
            let expectedTime = filtered[0].time;
            
            for (let i = 0; i < filtered.length; i++) {
                const candle = { ...filtered[i] };
                const candleDate = new Date(candle.time * 1000);
                const candleDay = candleDate.getUTCDay();
                
                // Handle weekend jumps like TradingView
                if (lastTradingDay === 5 && candleDay === 0) {
                    // Jump from Friday to Sunday (maintain exact times)
                    // This skips Saturday completely while maintaining a continuous series
                    // TradingView shows the last Friday candle connected directly to the first Sunday candle
                    expectedTime = candle.time - interval;
                }
                
                // Save original time for reference
                candle.originalTime = candle.time;
                
                // Set the continuous time - preserves exact trading times
                candle.time = expectedTime;
                
                // Update expected time for next candle
                expectedTime += interval;
                
                // Update last trading day
                lastTradingDay = candleDay;
                
                continuous.push(candle);
            }
        } else {
            // For daily timeframes, keep original behavior
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
        }
        
        return continuous;
    }
    
    /**
     * Detect the interval between candles
     * @param {Array} candles - Array of candle objects
     * @returns {number} - Interval in seconds
     */
    detectInterval(candles) {
        if (candles.length < 2) {
            return 3600; // Default to 1 hour
        }
        
        // Calculate intervals between consecutive candles
        const intervals = [];
        for (let i = 1; i < Math.min(10, candles.length); i++) {
            // Only consider consecutive trading sessions
            if (this.isConsecutiveTrading(candles[i-1].time, candles[i].time)) {
                intervals.push(candles[i].time - candles[i-1].time);
            }
        }
        
        if (intervals.length === 0) {
            return 3600; // Default to 1 hour
        }
        
        // Find the most common interval
        return this.mode(intervals);
    }
    
    /**
     * Check if two timestamps are in consecutive trading sessions
     * @param {number} time1 - First timestamp
     * @param {number} time2 - Second timestamp
     * @returns {boolean} - True if consecutive
     */
    isConsecutiveTrading(time1, time2) {
        // Convert to Date objects
        const date1 = new Date(time1 * 1000);
        const date2 = new Date(time2 * 1000);
        
        // Check if they're on the same day
        if (date1.toISOString().split('T')[0] === date2.toISOString().split('T')[0]) {
            return true;
        }
        
        // Check if they're on consecutive trading days
        const daysDiff = Math.floor((time2 - time1) / 86400);
        return daysDiff === 1 || 
               (date1.getUTCDay() === 5 && date2.getUTCDay() === 0); // Friday to Sunday
    }
    
    /**
     * Find the most common value in an array
     * @param {Array} arr - Array of numbers
     * @returns {number} - Most common value
     */
    mode(arr) {
        const counts = {};
        let maxCount = 0;
        let maxValue = arr[0];
        
        for (const value of arr) {
            counts[value] = (counts[value] || 0) + 1;
            if (counts[value] > maxCount) {
                maxCount = counts[value];
                maxValue = value;
            }
        }
        
        return maxValue;
    }
    
    /**
     * Add a custom holiday to the list
     * @param {string} dateStr - Date string in YYYY-MM-DD format
     */
    addHoliday(dateStr) {
        this.holidays.add(dateStr);
    }
    
    /**
     * Guess the timeframe from candle interval
     * @param {number} interval - Interval in seconds
     * @returns {string} - Timeframe code
     */
    guessTimeframe(interval) {
        // Convert to minutes
        const minutes = interval / 60;
        
        if (minutes === 1) return '1m';
        if (minutes === 5) return '5m';
        if (minutes === 15) return '15m';
        if (minutes === 30) return '30m';
        if (minutes === 60) return '1h';
        if (minutes === 240) return '4h';
        if (minutes === 1440) return '1d';
        
        // Default to the closest timeframe
        const timeframes = [1, 5, 15, 30, 60, 240, 1440];
        let closest = timeframes.reduce((prev, curr) => 
            Math.abs(curr - minutes) < Math.abs(prev - minutes) ? curr : prev
        );
        
        // Convert back to string format
        if (closest === 1) return '1m';
        if (closest === 5) return '5m';
        if (closest === 15) return '15m';
        if (closest === 30) return '30m';
        if (closest === 60) return '1h';
        if (closest === 240) return '4h';
        if (closest === 1440) return '1d';
        
        return '1h'; // Default
    }
}

// For module imports
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ForexSessionFilter;
} 
// For browser/script tag usage
else if (typeof window !== 'undefined') {
    window.ForexSessionFilter = ForexSessionFilter;
}