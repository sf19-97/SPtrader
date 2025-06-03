/**
 * Configuration management utilities for DevTools CLI
 */

const fs = require('fs-extra');
const path = require('path');
const { input, confirm, select, number } = require('@inquirer/prompts');
const { execSync } = require('child_process');
const winston = require('winston');

// Create the logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'devtools-cli.log' })
  ]
});

/**
 * Run interactive configuration setup
 */
async function setupConfig() {
  console.log('DevTools CLI Configuration Setup');
  console.log('This will create a local configuration file with your settings.');
  console.log('');

  // Get answers to configuration questions
  const answers = {};
  
  // Get electron.host
  const electronHost = await input({
    message: 'Electron DevTools host:',
    default: 'localhost'
  });
  answers['electron'] = { host: electronHost };
  
  // Get electron.debugPort
  const debugPort = await number({
    message: 'Electron DevTools debug port:',
    default: 9222
  });
  answers.electron.debugPort = debugPort;
  
  // Get electron.processName
  const processName = await input({
    message: 'Electron process name pattern:',
    default: 'electron.*SPtrader'
  });
  answers.electron.processName = processName;
  
  // Get electron.timeout
  const timeout = await number({
    message: 'Connection timeout (ms):',
    default: 10000
  });
  answers.electron.timeout = timeout;
  
  // Get defaults.format
  const format = await select({
    message: 'Default output format:',
    choices: [
      { value: 'json', name: 'JSON' },
      { value: 'text', name: 'Text' }
    ],
    default: 'json'
  });
  answers['defaults'] = { format };
  
  // Get testConnection
  const testConnection = await confirm({
    message: 'Test connection to Electron process?',
    default: true
  });

  // Test connection if requested
  if (testConnection) {
    try {
      console.log('Testing connection to Electron process...');
      const found = testElectronProcess(answers.electron.processName);
      if (found) {
        console.log('✓ Electron process found!');
      } else {
        console.log('✗ Electron process not found. Is the app running?');
        const retry = await confirm({
        message: 'Would you like to retry with a different process pattern?',
        default: true
      });
      if (retry) {
          return setupConfig();
        }
      }
    } catch (error) {
      console.log(`✗ Error testing connection: ${error.message}`);
      const retry = await confirm({
        message: 'Would you like to retry with different settings?',
        default: true
      });
      if (retry) {
        return setupConfig();
      }
    }
  }

  // Create config file
  const configFile = path.join(__dirname, '../config/local.json');
  
  // Remove testConnection property
  delete answers.testConnection;
  
  // Save the config
  fs.writeJsonSync(configFile, answers, { spaces: 2 });
  console.log(`Configuration saved to ${configFile}`);
  
  console.log('');
  console.log('Setup complete!');
  console.log('Run `./devtools-cli.sh help` to see available commands.');
}

/**
 * Test if the Electron process is running
 * @param {string} processPattern - Process name pattern to match
 * @returns {boolean} - True if process is found
 */
function testElectronProcess(processPattern) {
  try {
    // Use different commands based on platform
    let command;
    if (process.platform === 'win32') {
      command = `tasklist | findstr "${processPattern}"`;
    } else {
      command = `ps aux | grep -E "${processPattern}" | grep -v grep`;
    }
    
    const output = execSync(command, { encoding: 'utf8' });
    return output.trim().length > 0;
  } catch (error) {
    // Command failed or no matching process
    return false;
  }
}

/**
 * Load configuration
 * @returns {Object} - Configuration object
 */
function loadConfig() {
  try {
    // Determine NODE_ENV
    const env = process.env.NODE_ENV || 'development';
    
    // Load default config
    const defaultConfig = require('../config/default.json');
    
    // Load environment config
    let envConfig = {};
    try {
      envConfig = require(`../config/${env}.json`);
    } catch (error) {
      logger.warn(`No configuration found for environment: ${env}`);
    }
    
    // Load local config
    let localConfig = {};
    try {
      localConfig = require('../config/local.json');
    } catch (error) {
      // Local config is optional
    }
    
    // Merge configs (local overrides environment overrides default)
    return { ...defaultConfig, ...envConfig, ...localConfig };
  } catch (error) {
    logger.error('Failed to load configuration', error);
    return {};
  }
}

module.exports = {
  setupConfig,
  testElectronProcess,
  loadConfig,
  logger
};