/**
 * Fix for inconsistent initial data range across timeframes
 * This replaces the simple date subtraction with intelligent range selection
 */

async function getSmartInitialRange(symbol, timeframe, apiBase) {
  // First, get the data range
  const rangeResponse = await fetch(`${apiBase}/data/range?symbol=${symbol}`);
  const dataRange = await rangeResponse.json();
  
  const dbStart = new Date(dataRange.start);
  const dbEnd = new Date(dataRange.end);
  
  console.log(`Database range: ${dbStart.toISOString()} to ${dbEnd.toISOString()}`);
  
  // Query to find the latest day with substantial data (>10k ticks)
  const query = `
    WITH daily_counts AS (
      SELECT 
        DATE_TRUNC('day', timestamp) as day,
        COUNT(*) as tick_count
      FROM market_data_v2
      WHERE symbol = '${symbol}'
        AND timestamp >= '${dbEnd.toISOString()}'::timestamp - INTERVAL '30 days'
      GROUP BY day
    )
    SELECT day 
    FROM daily_counts 
    WHERE tick_count > 10000 
    ORDER BY day DESC 
    LIMIT 1
  `;
  
  try {
    const response = await fetch(`http://localhost:9000/exec?query=${encodeURIComponent(query)}`);
    const result = await response.json();
    
    let effectiveEnd = dbEnd;
    
    if (result.dataset && result.dataset.length > 0) {
      // Use the latest day with substantial data
      effectiveEnd = new Date(result.dataset[0][0]);
      // Add 23:59:59 to get end of day
      effectiveEnd.setHours(23, 59, 59, 999);
      console.log(`Using effective end with substantial data: ${effectiveEnd.toISOString()}`);
    }
    
    // Now calculate start based on timeframe, ensuring we have enough data
    const start = new Date(effectiveEnd);
    
    // More intelligent range selection based on timeframe
    switch(timeframe) {
      case '1m':
      case '5m':
        // For minute charts, show last 3 trading days worth
        start.setDate(start.getDate() - 5); // 5 calendar days = ~3 trading days
        break;
        
      case '15m':
      case '30m':
        // Show 2 weeks for medium timeframes
        start.setDate(start.getDate() - 14);
        break;
        
      case '1h':
        // Show 2 months for hourly
        start.setMonth(start.getMonth() - 2);
        break;
        
      case '4h':
        // Show 6 months for 4-hour
        start.setMonth(start.getMonth() - 6);
        break;
        
      case '1d':
        // Show full available range for daily
        return { start: dbStart, end: effectiveEnd };
        
      default:
        start.setMonth(start.getMonth() - 1);
    }
    
    // Ensure start isn't before data begins
    if (start < dbStart) {
      start.setTime(dbStart.getTime());
    }
    
    console.log(`Smart range for ${timeframe}: ${start.toISOString()} to ${effectiveEnd.toISOString()}`);
    
    return { start, end: effectiveEnd };
    
  } catch (error) {
    console.error('Failed to get smart range, falling back to simple calculation', error);
    
    // Fallback to original logic
    const end = new Date(dbEnd);
    const start = new Date(dbEnd);
    
    switch(timeframe) {
      case '1m':
      case '5m':
        start.setDate(start.getDate() - 5);
        break;
      case '15m':
      case '30m':
        start.setDate(start.getDate() - 14);
        break;
      case '1h':
        start.setMonth(start.getMonth() - 2);
        break;
      case '4h':
        start.setMonth(start.getMonth() - 6);
        break;
      case '1d':
        start.setFullYear(start.getFullYear() - 1);
        break;
      default:
        start.setMonth(start.getMonth() - 1);
    }
    
    return { start, end };
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = getSmartInitialRange;
}