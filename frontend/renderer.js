// API configuration
const API_BASE = 'http://localhost:8080/api/v1';

// Chart instance
let chart = null;
let candleSeries = null;

// Initialize chart
function initChart() {
  const chartContainer = document.getElementById('chart');
  
  chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    layout: {
      background: { color: '#1a1a1a' },
      textColor: '#d9d9d9',
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: {
        width: 1,
        color: '#758696',
        style: LightweightCharts.LineStyle.Dashed,
        labelVisible: true,
      },
      horzLine: {
        width: 1,
        color: '#758696',
        style: LightweightCharts.LineStyle.Dashed,
        labelVisible: true,
      },
    },
    grid: {
      vertLines: { color: '#2a2a2a' },
      horzLines: { color: '#2a2a2a' },
    },
    timeScale: {
      borderColor: '#3a3a3a',
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 12,
      barSpacing: 3,
      fixLeftEdge: false,
      fixRightEdge: false,
      preserveBarSpacing: true,  // Keep bar spacing consistent
      lockVisibleTimeRangeOnResize: true,
      tickMarkFormatter: (time, tickMarkType, locale) => {
        // Custom formatter to show UTC time
        const date = new Date(time * 1000);
        
        // For intraday, show UTC time
        if (tickMarkType < 4) {
          const hours = date.getUTCHours().toString().padStart(2, '0');
          const minutes = date.getUTCMinutes().toString().padStart(2, '0');
          return `${hours}:${minutes}`;
        }
        
        // For daily and above, show UTC date
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[date.getUTCMonth()]} ${date.getUTCDate()}`;
      },
    },
    rightPriceScale: {
      borderColor: '#3a3a3a',
      scaleMargins: {
        top: 0.2,    // More space at top
        bottom: 0.2,  // More space at bottom
      },
      mode: 0,  // Normal mode (not percentage)
      autoScale: false,  // Don't auto-scale on data updates
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: true,
    },
    handleScale: {
      axisPressedMouseMove: {
        time: true,
        price: true,
      },
      mouseWheel: true,
      pinch: true,
    },
  });

  // Create candlestick series
  candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
    priceFormat: {
      type: 'price',
      precision: 5,
      minMove: 0.00001,
    },
  });

  // Handle resize
  window.addEventListener('resize', () => {
    chart.applyOptions({
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
    });
  });
  
  // Track crosshair movement for OHLCV display
  chart.subscribeCrosshairMove((param) => {
    if (!param || !param.time || !param.seriesData || !window.candleData) {
      return;
    }
    
    const data = param.seriesData.get(candleSeries);
    if (!data) return;
    
    // Find the matching candle from raw data for volume
    const timestamp = new Date(param.time * 1000).toISOString();
    const candle = window.candleData.find(c => {
      const candleTime = new Date(c.timestamp).toISOString();
      return candleTime.startsWith(timestamp.substring(0, 19));
    });
    
    // Update OHLCV display
    document.getElementById('info-open').textContent = data.open.toFixed(5);
    document.getElementById('info-high').textContent = data.high.toFixed(5);
    document.getElementById('info-low').textContent = data.low.toFixed(5);
    document.getElementById('info-close').textContent = data.close.toFixed(5);
    document.getElementById('info-volume').textContent = candle ? candle.volume.toFixed(2) : '-';
    
    // Update close color based on direction
    const closeEl = document.getElementById('info-close');
    closeEl.style.color = data.close >= data.open ? '#26a69a' : '#ef5350';
  });
  
  // Track viewport changes for dynamic data loading
  let viewportTimer = null;
  window.currentDataRange = { start: null, end: null };
  
  chart.timeScale().subscribeVisibleTimeRangeChange(() => {
    if (viewportTimer) clearTimeout(viewportTimer);
    
    viewportTimer = setTimeout(() => {
      const timeRange = chart.timeScale().getVisibleRange();
      if (!timeRange || !timeRange.from || !timeRange.to) return;
      
      const symbol = document.getElementById('symbol').value;
      const timeframe = document.getElementById('timeframe').value;
      const viewStart = new Date(timeRange.from * 1000);
      const viewEnd = new Date(timeRange.to * 1000);
      
      console.log('=== VIEWPORT CHECK ===');
      console.log('Visible range:', viewStart.toISOString(), 'to', viewEnd.toISOString());
      
      // Skip if we don't have data loaded yet
      if (!window.currentDataRange.start || !window.currentDataRange.end) {
        console.log('No data range set yet, skipping...');
        return;
      }
      
      // Add buffer to load data beyond visible range
      const bufferMs = (viewEnd - viewStart) * 0.5; // 50% buffer on each side
      const fetchStart = new Date(viewStart.getTime() - bufferMs);
      const fetchEnd = new Date(viewEnd.getTime() + bufferMs);
      
      // Check if we need to fetch new data
      const needsBackwardData = fetchStart < window.currentDataRange.start;
      const needsForwardData = fetchEnd > window.currentDataRange.end;
      
      console.log('Current data:', window.currentDataRange.start.toISOString(), 'to', window.currentDataRange.end.toISOString());
      console.log('Needs backward:', needsBackwardData, 'Needs forward:', needsForwardData);
      
      if (needsBackwardData || needsForwardData) {
        console.log('Fetching new data...');
        console.log('Fetch range:', fetchStart.toISOString(), 'to', fetchEnd.toISOString());
        loadDataForRange(symbol, timeframe, fetchStart, fetchEnd);
      }
    }, 500); // Wait 500ms after scrolling stops
  });
}

// Load chart data
async function loadData() {
  const symbol = document.getElementById('symbol').value;
  const timeframe = document.getElementById('timeframe').value;
  const status = document.getElementById('status');
  
  try {
    status.textContent = 'Loading...';
    
    // First, get the available data range for the symbol
    const rangeResponse = await fetch(`${API_BASE}/data/range?symbol=${symbol}`);
    if (!rangeResponse.ok) {
      throw new Error(`Failed to get data range: ${rangeResponse.status}`);
    }
    
    const dataRange = await rangeResponse.json();
    console.log('Available data range:', dataRange);
    
    // Use the actual data range from the database
    const dbStart = new Date(dataRange.start);
    const dbEnd = new Date(dataRange.end);
    
    // Start with the most recent month of data
    const end = new Date(dbEnd);
    const start = new Date(dbEnd);
    start.setMonth(start.getMonth() - 1);
    
    const params = new URLSearchParams({
      symbol: symbol,
      tf: timeframe,
      resolution: timeframe,  // Force resolution to match timeframe
      start: start.toISOString(),
      end: end.toISOString()
    });
    
    const response = await fetch(`${API_BASE}/candles?${params}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.candles || data.candles.length === 0) {
      status.textContent = 'No data available';
      candleSeries.setData([]);
      return;
    }
    
    // Convert data to chart format
    const chartData = data.candles
      .filter((candle, index, self) => {
        // Remove duplicates based on timestamp
        return index === self.findIndex(c => c.timestamp === candle.timestamp);
      })
      .map(candle => ({
        time: new Date(candle.timestamp).getTime() / 1000,
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }))
      .sort((a, b) => a.time - b.time);
    
    candleSeries.setData(chartData);
    status.textContent = `${symbol} - ${chartData.length} candles`;
    
    // Store raw candle data for OHLCV display
    window.candleData = data.candles;
    
    // Store the loaded data range
    window.currentDataRange = { start: new Date(start), end: new Date(end) };
    
    // Fit content on initial load
    if (!window.hasInitialLoad) {
      window.hasInitialLoad = true;
      chart.priceScale('right').applyOptions({ autoScale: true });
      chart.timeScale().fitContent();
      // After fitting, disable auto-scale
      setTimeout(() => {
        chart.priceScale('right').applyOptions({ autoScale: false });
      }, 100);
    }
    
    // Show OHLCV info
    document.getElementById('ohlc-info').style.display = 'block';
    
  } catch (error) {
    console.error('Error loading data:', error);
    status.textContent = `Error: ${error.message}`;
  }
}

// Load data for specific date range with lazy loading
async function loadDataForRange(symbol, timeframe, start, end) {
  const status = document.getElementById('status');
  
  // Store the current range
  window.currentDataRange = { start, end };
  
  try {
    status.textContent = 'Loading range data...';
    
    const params = new URLSearchParams({
      symbol: symbol,
      tf: timeframe,
      resolution: timeframe,
      start: start.toISOString(),
      end: end.toISOString()
    });
    
    // Use lazy loading endpoint
    const response = await fetch(`${API_BASE}/candles/lazy?${params}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Handle 202 response (data is being fetched or no data)
    if (response.status === 202) {
      if (data.status === 'fetching') {
        status.textContent = 'Fetching historical data from Dukascopy...';
        // Retry after delay
        setTimeout(() => {
          loadDataForRange(symbol, timeframe, start, end);
        }, 3000);
        return;
      } else if (data.status === 'no_data') {
        status.textContent = 'No data available - triggering Dukascopy fetch...';
        
        // Trigger data fetch
        const ensureResponse = await fetch(`${API_BASE}/data/ensure`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            symbol: symbol,
            start: start.toISOString(),
            end: end.toISOString()
          })
        });
        
        if (ensureResponse.ok) {
          status.textContent = 'Fetching from Dukascopy... (this may take 30-60 seconds)';
          // Wait and retry
          setTimeout(() => {
            loadDataForRange(symbol, timeframe, start, end);
          }, 10000); // Wait 10 seconds for fetch
        }
        return;
      }
    }
    
    if (!data.candles || data.candles.length === 0) {
      // Try regular endpoint if lazy loading has no data
      const regularResponse = await fetch(`${API_BASE}/candles?${params}`);
      if (regularResponse.ok) {
        const regularData = await regularResponse.json();
        if (regularData.candles && regularData.candles.length > 0) {
          mergeAndDisplayData(regularData.candles, symbol);
          return;
        }
      }
      
      status.textContent = 'No data available for this range';
      return;
    }
    
    // Process and display data
    mergeAndDisplayData(data.candles, symbol);
    
  } catch (error) {
    console.error('Error loading range data:', error);
    status.textContent = `Error: ${error.message}`;
  }
}

// Merge new data with existing chart data
function mergeAndDisplayData(newCandles, symbol) {
  const status = document.getElementById('status');
  
  // Save current viewport before updating data
  const currentViewport = chart.timeScale().getVisibleRange();
  const visibleLogicalRange = chart.timeScale().getVisibleLogicalRange();
  
  // Get existing chart data
  const existingData = window.candleData || [];
  
  // Create a map for efficient merging
  const dataMap = new Map();
  
  // Add existing data to map
  existingData.forEach(candle => {
    dataMap.set(candle.timestamp, candle);
  });
  
  // Add new data to map (overwrites duplicates)
  newCandles.forEach(candle => {
    dataMap.set(candle.timestamp, candle);
  });
  
  // Convert back to array and sort
  const mergedData = Array.from(dataMap.values())
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  
  // Store merged data
  window.candleData = mergedData;
  
  // Convert to chart format with deduplication
  const chartData = mergedData
    .filter((candle, index, self) => {
      return index === self.findIndex(c => c.timestamp === candle.timestamp);
    })
    .map(candle => ({
      time: new Date(candle.timestamp).getTime() / 1000,
      open: parseFloat(candle.open),
      high: parseFloat(candle.high),
      low: parseFloat(candle.low),
      close: parseFloat(candle.close),
    }))
    .sort((a, b) => a.time - b.time);
  
  // Update chart
  candleSeries.setData(chartData);
  
  // Always restore viewport to prevent jumping
  if (currentViewport && currentViewport.from && currentViewport.to) {
    // Force the time scale to stay exactly where it was
    setTimeout(() => {
      chart.timeScale().setVisibleRange(currentViewport);
    }, 0);
  }
  
  status.textContent = `${symbol} - ${chartData.length} candles`;
  
  // Show OHLCV info if not visible
  document.getElementById('ohlc-info').style.display = 'block';
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  initChart();
  loadData();
  
  // Event listeners with debouncing
  let changeTimer = null;
  
  const debouncedLoad = () => {
    if (changeTimer) clearTimeout(changeTimer);
    changeTimer = setTimeout(() => {
      candleSeries.setData([]);
      document.getElementById('status').textContent = 'Loading...';
      loadData();
    }, 100);
  };
  
  document.getElementById('symbol').addEventListener('change', debouncedLoad);
  document.getElementById('timeframe').addEventListener('change', debouncedLoad);
  
  // Fit chart button
  document.getElementById('fit-chart').addEventListener('click', () => {
    // Temporarily enable auto-scale
    chart.priceScale('right').applyOptions({ autoScale: true });
    chart.timeScale().fitContent();
    
    // After a brief moment, disable auto-scale again
    setTimeout(() => {
      chart.priceScale('right').applyOptions({ autoScale: false });
    }, 100);
  });
});