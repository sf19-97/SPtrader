const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function measure() {
  console.log('Measuring performance...');
  let client;
  
  try {
    client = await CDP();
    const { Performance, Runtime } = client;
    
    // Enable domains
    await Performance.enable();
    
    // Get performance metrics
    const { metrics } = await Performance.getMetrics();
    
    // Get memory usage
    const memoryInfo = await Runtime.evaluate({
      expression: 'window.performance.memory',
      returnByValue: true
    });
    
    // Collect FPS information
    const fpsInfo = await Runtime.evaluate({
      expression: `
        (() => {
          let fps = 0;
          let frameTimes = [];
          let lastFrameTime = performance.now();
          
          requestAnimationFrame(function measure() {
            const now = performance.now();
            frameTimes.push(now - lastFrameTime);
            if (frameTimes.length > 60) {
              frameTimes.shift();
            }
            
            lastFrameTime = now;
            fps = 1000 / (frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length);
            
            // Stop after collecting enough data
            if (frameTimes.length >= 60) {
              return {
                fps: Math.round(fps),
                frameTimes: frameTimes
              };
            }
            
            requestAnimationFrame(measure);
          });
          
          // Return a placeholder that will be updated
          return "Measuring FPS...";
        })()
      `,
      returnByValue: true
    });
    
    // Get timing data
    const timingInfo = await Runtime.evaluate({
      expression: 'window.performance.timing',
      returnByValue: true
    });
    
    // Save all performance data
    const performanceData = {
      metrics,
      memory: memoryInfo.result.value,
      timing: timingInfo.result.value,
      timestamp: new Date().toISOString()
    };
    
    const outputPath = path.join(__dirname, '../output/performance.json');
    fs.writeJsonSync(outputPath, performanceData, { spaces: 2 });
    
    console.log(`Performance measurement complete. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error measuring performance:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { measure };