const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function dump() {
  console.log('Dumping application state...');
  let client;
  
  try {
    client = await CDP();
    const { Runtime } = client;
    
    // Get global variables
    const globalState = await Runtime.evaluate({
      expression: `
        (() => {
          // Collect relevant global variables
          const state = {
            chart: window.chart ? {
              exists: true,
              timeScale: window.chart.timeScale ? true : false
            } : null,
            candleSeries: window.candleSeries ? true : null,
            virtualDataManager: window.virtualDataManager ? {
              exists: true,
              windowSize: window.virtualDataManager.windowSize
            } : null,
            forexSessionFilter: window.forexSessionFilter ? true : null,
            smartScaling: window.smartScaling ? true : null,
            candleData: window.candleData ? {
              length: window.candleData.length,
              sampleData: window.candleData.slice(0, 2)
            } : null,
            symbol: document.getElementById('symbol')?.value,
            timeframe: document.getElementById('timeframe')?.value,
            windowDimensions: {
              width: window.innerWidth,
              height: window.innerHeight
            }
          };
          
          return state;
        })()
      `,
      returnByValue: true
    });
    
    // Save state
    const outputPath = path.join(__dirname, '../output/app-state.json');
    fs.writeJsonSync(outputPath, globalState.result.value, { spaces: 2 });
    
    console.log(`Application state dumped. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error dumping application state:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { dump };