/**
 * Configuration management utilities for QuestDB CLI
 */

const fs = require('fs-extra');
const path = require('path');
const { input, password, confirm, select, number } = require('@inquirer/prompts');
const chalk = require('chalk');
const { spawn } = require('child_process');

/**
 * Run interactive configuration setup
 */
async function setupConfig() {
  console.log(chalk.bold('QuestDB CLI Configuration Setup'));
  console.log(chalk.gray('This will create a local configuration file with your settings.'));
  console.log('');

  // Get answers to configuration questions
  const answers = {};
  
  // Get database settings
  const dbHost = await input({
    message: 'QuestDB host:',
    default: 'localhost'
  });
  answers['database'] = { host: dbHost };
  
  const httpPort = await number({
    message: 'QuestDB HTTP port:',
    default: 9000
  });
  answers.database.httpPort = httpPort;
  
  const ilpPort = await number({
    message: 'QuestDB ILP port:',
    default: 9009
  });
  answers.database.ilpPort = ilpPort;
  
  const pgPort = await number({
    message: 'QuestDB PG wire protocol port:',
    default: 8812
  });
  answers.database.pgPort = pgPort;
  
  const username = await input({
    message: 'Database username:',
    default: 'admin'
  });
  answers.database.username = username;
  
  const pwd = await password({
    message: 'Database password:',
    default: 'quest'
  });
  answers.database.password = pwd;
  
  // Get API settings
  const apiBaseUrl = await input({
    message: 'SPtrader API base URL:',
    default: 'http://localhost:8080/api/v1'
  });
  answers['api'] = { baseUrl: apiBaseUrl };
  
  // Get default format
  const format = await select({
    message: 'Default output format:',
    choices: [
      { value: 'table', name: 'Table' },
      { value: 'json', name: 'JSON' },
      { value: 'csv', name: 'CSV' }
    ],
    default: 'table'
  });
  answers['defaults'] = { format };
  
  // Test connection?
  const testConnection = await confirm({
    message: 'Test database connection?',
    default: true
  });

  // Test connection if requested
  if (testConnection) {
    try {
      console.log(chalk.gray('Testing database connection...'));
      await testConnection(answers.database);
      console.log(chalk.green('✓ Connection successful!'));
    } catch (error) {
      console.log(chalk.red(`✗ Connection failed: ${error.message}`));
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
  console.log(chalk.green(`Configuration saved to ${configFile}`));
  
  // Ask if user wants to create a symlink
  const createSymlink = await confirm({
    message: 'Create symlink to make questdb-cli available globally?',
    default: false
  });

  if (createSymlink) {
    try {
      await createSymlink();
      console.log(chalk.green('✓ Symlink created successfully!'));
    } catch (error) {
      console.log(chalk.yellow(`Could not create symlink: ${error.message}`));
      console.log(chalk.gray('You can still run the CLI using node questdb-cli.js'));
    }
  }

  console.log('');
  console.log(chalk.bold('Setup complete!'));
  console.log(chalk.gray('Run `node questdb-cli.js --help` to see available commands.'));
}

/**
 * Test database connection
 * @param {Object} dbConfig - Database configuration
 */
async function testConnection(dbConfig) {
  return new Promise((resolve, reject) => {
    // For now, just try to connect to the HTTP port
    const testUrl = `http://${dbConfig.host}:${dbConfig.httpPort}/exec?query=SELECT%201`;
    
    // Use a simple HTTP request
    const http = require('http');
    const req = http.get(testUrl, (res) => {
      if (res.statusCode === 200) {
        resolve();
      } else {
        reject(new Error(`HTTP status ${res.statusCode}`));
      }
    });
    
    req.on('error', (err) => {
      reject(err);
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Connection timeout'));
    });
  });
}

/**
 * Create symlink to make CLI globally available
 */
async function createSymlink() {
  return new Promise((resolve, reject) => {
    const cliPath = path.join(__dirname, '../questdb-cli.js');
    const symPath = '/usr/local/bin/questdb-cli';
    
    // Make the script executable
    fs.chmodSync(cliPath, '755');
    
    const cmd = spawn('sudo', ['ln', '-sf', cliPath, symPath]);
    
    cmd.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command exited with code ${code}`));
      }
    });
    
    cmd.on('error', (err) => {
      reject(err);
    });
  });
}

module.exports = {
  setupConfig,
  testConnection
};