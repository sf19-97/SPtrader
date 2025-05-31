// Simple test of the ForexSessionFilter
const ForexSessionFilter = require('./forex_session_filter');

console.log("Creating filter instance...");
const filter = new ForexSessionFilter();

// Test market hours
const testTime = Math.floor(new Date(Date.UTC(2025, 4, 26, 12, 0, 0)).getTime() / 1000);
console.log(`Market open on 2025-05-26 12:00 UTC: ${filter.isMarketOpen(testTime)}`);

// Add holiday
console.log("Adding Whit Monday holiday (2025-05-26)...");
filter.addHoliday('2025-05-26');

// Re-test
console.log(`Market open on 2025-05-26 12:00 UTC after adding holiday: ${filter.isMarketOpen(testTime)}`);

console.log("Test complete!");