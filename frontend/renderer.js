// API configuration
const API_BASE = 'http://localhost:8080/api/v1';

// Chart instance
let chart = null;
let candleSeries = null;
let virtualDataManager = null;
let forexSessionFilter = null;

// Import or include the ForexSessionFilter
const ForexSessionFilter = window.ForexSessionFilter || {
  createContinuousView: (candles) => candles // Fallback if not loaded
};

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
        const date = new Date(time * 1000);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        // tickMarkType indicates the significance of the time point:
        // 0 = year, 1 = month, 2 = day of month, 3 = day of week, 4 = hour, 5 = minute
        
        // Year tick
        if (tickMarkType === 0) {
          return date.getUTCFullYear().toString();
        }
        
        // Month tick
        if (tickMarkType === 1) {
          const month = months[date.getUTCMonth()];
          const year = date.getUTCFullYear().toString().slice(-2);
          return `${month} '${year}`;
        }
        
        // Day tick
        if (tickMarkType === 2) {
          const day = date.getUTCDate();
          const month = months[date.getUTCMonth()];
          const year = date.getUTCFullYear().toString().slice(-2);
          
          // Show year on January 1st
          if (date.getUTCMonth() === 0 && day === 1) {
            return `${day} ${month} '${year}`;
          }
          
          // Show month and day on 1st of each month
          if (day === 1) {
            return `${day} ${month}`;
          }
          
          // Otherwise just show day and month
          return `${day} ${month}`;
        }
        
        // Hour/minute ticks - check the current timeframe
        const timeframe = document.getElementById('timeframe')?.value || '1h';
        const hours = date.getUTCHours().toString().padStart(2, '0');
        const minutes = date.getUTCMinutes().toString().padStart(2, '0');
        
        // For daily timeframe, always show dates
        if (timeframe === '1d') {
          const day = date.getUTCDate();
          const month = months[date.getUTCMonth()];
          return `${day} ${month}`;
        }
        
        // For intraday timeframes
        if (tickMarkType >= 3) {
          // At midnight, show the date
          if (hours === '00' && minutes === '00') {
            const day = date.getUTCDate();
            const month = months[date.getUTCMonth()];
            const year = date.getUTCFullYear().toString().slice(-2);
            
            // Include year at significant dates
            if (date.getUTCDate() === 1 || tickMarkType === 2) {
              return `${day} ${month} '${year}`;
            }
            return `${day} ${month}`;
          }
          
          // Otherwise show time
          return `${hours}:${minutes}`;
        }
        
        // Default format
        return `${date.getUTCDate()} ${months[date.getUTCMonth()]}`;
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
    // Ensure gaps are handled properly
    priceLineVisible: false,
    lastValueVisible: true,
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
    if (!param || !param.time || !param.seriesData || !virtualDataManager) {
      return;
    }
    
    const data = param.seriesData.get(candleSeries);
    if (!data) return;
    
    // For virtual scrolling, we already have volume in the data
    // since VirtualDataManager window contains the full candle data
    const candle = { volume: 0 }; // Default if not found
    
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
  
  // Initialize Virtual Data Manager
  // ⚠️ CRITICAL: DO NOT REDUCE THIS VALUE! ⚠️
  // The large window size (2M) is intentional to ensure we show ALL historical data.
  // Reducing this value will cause older data (before March 2024) to be hidden.
  virtualDataManager = new VirtualDataManager(2000000); // Keep 2 million candles in memory for full historical data
  
  // Track viewport changes with virtual scrolling
  let viewportTimer = null;
  
  chart.timeScale().subscribeVisibleTimeRangeChange(() => {
    if (viewportTimer) clearTimeout(viewportTimer);
    
    viewportTimer = setTimeout(() => {
      const timeRange = chart.timeScale().getVisibleRange();
      if (!timeRange || !virtualDataManager) return;
      
      // Let VirtualDataManager handle the viewport update
      virtualDataManager.updateViewport(timeRange);
      
      // Update status
      const info = virtualDataManager.getInfo();
      const status = document.getElementById('status');
      if (status && info.windowSize > 0) {
        status.textContent = `${virtualDataManager.symbol} - ${info.windowSize} candles in view (Virtual Scrolling)`;
      }
    }, 300); // Reduced to 300ms for more responsive updates
  });
}

// Load chart data with full date range for all timeframes
async function loadData() {
  const symbol = document.getElementById('symbol').value;
  const timeframe = document.getElementById('timeframe').value;
  const status = document.getElementById('status');
  
  try {
    status.textContent = 'Loading data range...';
    
    // Step 1: Get the complete available data range for this symbol
    const rangeResponse = await fetch(`${API_BASE}/data/range?symbol=${symbol}`);
    if (!rangeResponse.ok) {
      throw new Error(`Failed to get data range: ${rangeResponse.status}`);
    }
    
    const dataRange = await rangeResponse.json();
    console.log('Available data range:', dataRange);
    
    // Step 2: Use the FULL date range - no filtering
    const fullStart = new Date(dataRange.start);
    const fullEnd = new Date(dataRange.end);
    
    console.log(`Loading FULL data range: ${fullStart.toISOString()} to ${fullEnd.toISOString()}`);
    
    // Step 3: Clear any existing data
    if (virtualDataManager) {
      virtualDataManager.clear();
    }
    
    // Initialize virtual data manager with chart
    virtualDataManager.init(chart, candleSeries, symbol, timeframe);
    
    // Step 4: Load all data into virtual data manager
    await virtualDataManager.loadWindowData(fullStart, fullEnd, fullStart, fullEnd);
    
    // Step 5: Set the visible range to show ALL data
    const startTime = fullStart.getTime() / 1000;
    const endTime = fullEnd.getTime() / 1000;
    
    chart.timeScale().setVisibleRange({
      from: startTime,
      to: endTime
    });
    
    // Fit content on initial load
    chart.priceScale('right').applyOptions({ autoScale: true });
    chart.timeScale().fitContent();
    // After fitting, disable auto-scale
    setTimeout(() => {
      chart.priceScale('right').applyOptions({ autoScale: false });
    }, 100);
    
    // Show OHLCV info
    document.getElementById('ohlc-info').style.display = 'block';
    
    // Update status
    const info = virtualDataManager.getInfo();
    status.textContent = `${symbol} - ${info.windowSize} candles in view (Virtual Scrolling)`;
    
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
  
  // Apply forex session filter to create continuous view without gaps
  if (forexSessionFilter) {
    // Use the forex session filter to create a continuous view
    const continuousData = forexSessionFilter.createContinuousView(chartData);
    console.log(`Filtered ${chartData.length} candles to ${continuousData.length} trading candles`);
    chartData = continuousData;
  } else {
    console.log('Forex session filter not loaded, showing data with gaps');
  }
  
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

// Emergency fallback function to force loading ALL data
async function forceLoadAllData() {
  const symbol = document.getElementById('symbol').value;
  const timeframe = document.getElementById('timeframe').value;
  const status = document.getElementById('status');
  
  try {
    status.textContent = 'EMERGENCY MODE: Loading ALL available data...';
    
    // Force start/end dates to cover all possible data
    const forcedStart = new Date('2020-01-01T00:00:00.000Z'); // Way before your data starts
    const forcedEnd = new Date(); // Current time
    
    console.log(`Forcing MAXIMUM date range: ${forcedStart.toISOString()} to ${forcedEnd.toISOString()}`);
    
    // Make direct request to ensure we get ALL data
    const params = new URLSearchParams({
      symbol: symbol,
      tf: timeframe,
      start: forcedStart.toISOString(),
      end: forcedEnd.toISOString()
    });
    
    // Try various endpoints until one works
    let data = null;
    let endpoint = '';
    
    // Try regular endpoint first
    try {
      endpoint = `${API_BASE}/candles?${params}`;
      console.log(`Trying endpoint: ${endpoint}`);
      const response = await fetch(endpoint);
      
      if (response.ok) {
        data = await response.json();
        if (data.candles && data.candles.length > 0) {
          console.log(`Success with endpoint: ${endpoint}`);
        } else {
          data = null;
        }
      }
    } catch (err) {
      console.error(`Failed with endpoint: ${endpoint}`, err);
    }
    
    // If that fails, try lazy endpoint
    if (!data) {
      try {
        endpoint = `${API_BASE}/candles/lazy?${params}`;
        console.log(`Trying endpoint: ${endpoint}`);
        const response = await fetch(endpoint);
        
        if (response.ok) {
          data = await response.json();
          if (data.candles && data.candles.length > 0) {
            console.log(`Success with endpoint: ${endpoint}`);
          } else {
            data = null;
          }
        }
      } catch (err) {
        console.error(`Failed with endpoint: ${endpoint}`, err);
      }
    }
    
    // Last resort - try native endpoint
    if (!data) {
      try {
        endpoint = `${API_BASE}/candles/native?${params}`;
        console.log(`Trying endpoint: ${endpoint}`);
        const response = await fetch(endpoint);
        
        if (response.ok) {
          data = await response.json();
          if (data.candles && data.candles.length > 0) {
            console.log(`Success with endpoint: ${endpoint}`);
          } else {
            data = null;
          }
        }
      } catch (err) {
        console.error(`Failed with endpoint: ${endpoint}`, err);
      }
    }
    
    if (!data || !data.candles || data.candles.length === 0) {
      status.textContent = 'EMERGENCY MODE FAILED: No data available from any endpoint';
      return;
    }
    
    // Convert to chart format
    const chartData = data.candles
      .map(candle => ({
        time: new Date(candle.timestamp).getTime() / 1000,
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }))
      .sort((a, b) => a.time - b.time);
    
    // Update chart directly (bypass virtual data manager)
    candleSeries.setData(chartData);
    
    // Apply forex session filter if available
    if (forexSessionFilter) {
      const continuousData = forexSessionFilter.createContinuousView(chartData);
      console.log(`Emergency mode: Filtered ${chartData.length} candles to ${continuousData.length} trading candles`);
      chartData = continuousData;
    }
    
    // Update chart
    candleSeries.setData(chartData);
    
    // Set the visible range and fit content
    chart.timeScale().fitContent();
    
    status.textContent = `EMERGENCY MODE: ${symbol} ${timeframe} - Loaded ${chartData.length} candles directly`;
    
  } catch (error) {
    console.error('EMERGENCY MODE ERROR:', error);
    status.textContent = `EMERGENCY MODE FAILED: ${error.message}`;
  }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  // Initialize the forex session filter
  try {
    // Create the forex session filter instance
    forexSessionFilter = new ForexSessionFilter();
    console.log('Forex session filter initialized');
    
    // Add custom holidays as needed
    forexSessionFilter.addHoliday('2025-05-26'); // Whit Monday
  } catch (e) {
    console.error('Failed to initialize forex session filter:', e);
  }
  
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
  
  // Add emergency button to force load all data
  const headerContainer = document.getElementById('header');
  const emergencyButton = document.createElement('button');
  emergencyButton.id = 'force-load-all';
  emergencyButton.textContent = 'EMERGENCY: Load ALL';
  emergencyButton.style.backgroundColor = '#ff5555';
  emergencyButton.style.color = 'white';
  emergencyButton.style.fontWeight = 'bold';
  emergencyButton.style.marginLeft = '10px';
  
  // Add the button to the header
  headerContainer.appendChild(emergencyButton);
  
  // Add event listener
  document.getElementById('force-load-all').addEventListener('click', forceLoadAllData);
});