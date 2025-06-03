const CDP = require('chrome-remote-interface');
const fs = require('fs-extra');
const path = require('path');

async function getLogs() {
  console.log('Retrieving console logs...');
  let client;
  
  try {
    client = await CDP();
    const { Console, Runtime } = client;
    
    // Enable domains
    await Console.enable();
    
    // Get existing logs
    const existingLogs = await Runtime.evaluate({
      expression: `
        (() => {
          if (!window.__consoleLogs) {
            return [];
          }
          return window.__consoleLogs;
        })()
      `,
      returnByValue: true
    });
    
    // Inject script to capture console logs
    await Runtime.evaluate({
      expression: `
        (() => {
          if (!window.__consoleLogs) {
            window.__consoleLogs = [];
            const originalConsole = {
              log: console.log,
              error: console.error,
              warn: console.warn,
              info: console.info
            };
            
            console.log = function() {
              window.__consoleLogs.push({
                type: 'log',
                timestamp: new Date().toISOString(),
                args: Array.from(arguments).map(arg => String(arg))
              });
              originalConsole.log.apply(console, arguments);
            };
            
            console.error = function() {
              window.__consoleLogs.push({
                type: 'error',
                timestamp: new Date().toISOString(),
                args: Array.from(arguments).map(arg => String(arg))
              });
              originalConsole.error.apply(console, arguments);
            };
            
            console.warn = function() {
              window.__consoleLogs.push({
                type: 'warn',
                timestamp: new Date().toISOString(),
                args: Array.from(arguments).map(arg => String(arg))
              });
              originalConsole.warn.apply(console, arguments);
            };
            
            console.info = function() {
              window.__consoleLogs.push({
                type: 'info',
                timestamp: new Date().toISOString(),
                args: Array.from(arguments).map(arg => String(arg))
              });
              originalConsole.info.apply(console, arguments);
            };
          }
        })()
      `,
      returnByValue: false
    });
    
    // Save output
    const logs = existingLogs.result.value || [];
    const outputPath = path.join(__dirname, '../output/console-logs.json');
    fs.writeJsonSync(outputPath, logs, { spaces: 2 });
    
    console.log(`Retrieved ${logs.length} console logs. Saved to ${outputPath}`);
  } catch (error) {
    console.error('Error retrieving console logs:', error);
  } finally {
    if (client) {
      await client.close();
    }
  }
}

module.exports = { getLogs };