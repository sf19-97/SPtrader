// test_forex_session_filter.js
// Simple test script for the forex session filter
// Created: May 31, 2025

// Import the ForexSessionFilter class
const fs = require('fs');
const path = require('path');

// Read the forex session filter file
const filterPath = path.join(__dirname, '../frontend/src/utils/forex_session_filter.js');
const filterCode = fs.readFileSync(filterPath, 'utf8');

// Create a sandbox to execute the code
const vm = require('vm');
const sandbox = { module: {} };
vm.createContext(sandbox);
vm.runInContext(filterCode, sandbox);

// Get the ForexSessionFilter class
let ForexSessionFilter;
if (sandbox.ForexSessionFilter) {
  ForexSessionFilter = sandbox.ForexSessionFilter;
} else if (sandbox.module.exports) {
  ForexSessionFilter = sandbox.module.exports;
} else {
  // Evaluate the code directly
  eval(filterCode);
}

const filter = new ForexSessionFilter();

// Test data - simulating candles from May 25-27, 2025 (including Whit Monday holiday)
const mockCandles = [];

// Generate mock candles (1-hour) for the test period
// May 25, 2025 (Sunday) - 00:00 to 23:00
for (let hour = 0; hour < 24; hour++) {
  const date = new Date(Date.UTC(2025, 4, 25, hour, 0, 0));
  mockCandles.push({
    time: Math.floor(date.getTime() / 1000),
    open: 1.0800 + (Math.random() * 0.0050),
    high: 1.0830 + (Math.random() * 0.0050),
    low: 1.0780 + (Math.random() * 0.0050),
    close: 1.0810 + (Math.random() * 0.0050),
    volume: Math.floor(Math.random() * 1000)
  });
}

// May 26, 2025 (Monday/Whit Monday) - 00:00 to 23:00
for (let hour = 0; hour < 24; hour++) {
  const date = new Date(Date.UTC(2025, 4, 26, hour, 0, 0));
  mockCandles.push({
    time: Math.floor(date.getTime() / 1000),
    open: 1.0810 + (Math.random() * 0.0050),
    high: 1.0840 + (Math.random() * 0.0050),
    low: 1.0790 + (Math.random() * 0.0050),
    close: 1.0820 + (Math.random() * 0.0050),
    volume: Math.floor(Math.random() * 1000)
  });
}

// May 27, 2025 (Tuesday) - 00:00 to 23:00
for (let hour = 0; hour < 24; hour++) {
  const date = new Date(Date.UTC(2025, 4, 27, hour, 0, 0));
  mockCandles.push({
    time: Math.floor(date.getTime() / 1000),
    open: 1.0820 + (Math.random() * 0.0050),
    high: 1.0850 + (Math.random() * 0.0050),
    low: 1.0800 + (Math.random() * 0.0050),
    close: 1.0830 + (Math.random() * 0.0050),
    volume: Math.floor(Math.random() * 1000)
  });
}

// Test 1: Check market hours detection
console.log('===== TEST 1: Market Hours Detection =====');
console.log('Sunday 21:00 UTC (Before open):', filter.isMarketOpen(mockCandles[21].time));
console.log('Sunday 22:00 UTC (Market open):', filter.isMarketOpen(mockCandles[22].time));
console.log('Monday 12:00 UTC (Regular hours):', filter.isMarketOpen(mockCandles[36].time));
console.log('May 26, 2025 (Whit Monday - Holiday):', !filter.holidays.has('2025-05-26'));

// Add the Whit Monday holiday
filter.addHoliday('2025-05-26');

// Re-test after adding holiday
console.log('May 26, 2025 (After adding holiday):', filter.holidays.has('2025-05-26'));
console.log('Monday 12:00 UTC (Holiday now):', filter.isMarketOpen(mockCandles[36].time));

// Test 2: Filter candles
console.log('\n===== TEST 2: Filtering Non-Trading Periods =====');
const originalCount = mockCandles.length;
const filtered = filter.filterCandles(mockCandles);
console.log(`Original candles: ${originalCount}`);
console.log(`Filtered candles: ${filtered.length}`);
console.log(`Removed ${originalCount - filtered.length} candles`);

// Test 3: Create continuous view
console.log('\n===== TEST 3: Creating Continuous View =====');
const continuous = filter.createContinuousView(mockCandles);
console.log(`Original candles: ${originalCount}`);
console.log(`Continuous view candles: ${continuous.length}`);

// Verify timeline is continuous
if (continuous.length > 1) {
  console.log('\nVerifying timeline continuity:');
  const interval = continuous[1].time - continuous[0].time;
  let isContiguous = true;
  
  for (let i = 1; i < continuous.length; i++) {
    if (continuous[i].time - continuous[i-1].time !== interval) {
      isContiguous = false;
      console.log(`Gap found at index ${i}: ${continuous[i].time - continuous[i-1].time} vs expected ${interval}`);
      break;
    }
  }
  
  if (isContiguous) {
    console.log(`✅ Timeline is continuous with interval of ${interval} seconds (${interval/60} minutes)`);
  } else {
    console.log('❌ Timeline has gaps');
  }
}

// Print a few example candles for comparison
console.log('\nOriginal vs Continuous Candles (First 3):');
for (let i = 0; i < 3 && i < continuous.length; i++) {
  const origTime = new Date(mockCandles[i].time * 1000).toISOString();
  const newTime = new Date(continuous[i].time * 1000).toISOString();
  const origTimeFromCont = continuous[i].originalTime ? 
    new Date(continuous[i].originalTime * 1000).toISOString() : 'undefined';
    
  console.log(`[${i}] Original: ${origTime}, Continuous: ${newTime}, Stored Original: ${origTimeFromCont}`);
}

console.log('\nTest complete! ✅');