#!/usr/bin/env node

const minimist = require('minimist');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);
const path = require('path');
const fs = require('fs-extra');
const winston = require('winston');

// Setup logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'devtools-cli.log' })
  ]
});

// Parse command line arguments
const argv = minimist(process.argv.slice(2));
const command = argv._[0] || 'help';
const param = argv._[1];

// Create output directory
fs.ensureDirSync(path.join(__dirname, 'output'));

async function main() {
  try {
    // Check if Electron app is running
    const { stdout } = await execAsync('pgrep -f "electron.*SPtrader"').catch(() => ({ stdout: '' }));
    if (!stdout.trim()) {
      console.error('SPtrader Electron app is not running');
      return;
    }
    
    // Handle commands
    switch (command) {
      case 'network':
        require('./commands/network').capture();
        break;
      case 'elements':
        require('./commands/elements').inspect(param);
        break;
      case 'console':
        require('./commands/console').getLogs();
        break;
      case 'performance':
        require('./commands/performance').measure();
        break;
      case 'state':
        require('./commands/state').dump();
        break;
      case 'help':
      default:
        showHelp();
    }
  } catch (error) {
    console.error('Error:', error.message);
    logger.error('Error executing command', { command, error: error.message });
  }
}

function showHelp() {
  console.log(`
DevTools CLI for SPtrader
Usage: node devtools.js [command] [params]

Commands:
  network          - Capture network requests
  elements [id]    - Inspect DOM elements (optionally by ID)
  console          - Get console logs
  performance      - Run performance analysis
  state            - Dump application state
  help             - Show this help
  `);
}

main();