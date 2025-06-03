#!/usr/bin/env node

/**
 * QuestDB CLI
 * Command-line interface for managing QuestDB databases
 * 
 * Created: May 31, 2025
 */

// Import dependencies
const { program } = require('commander');
const path = require('path');
const fs = require('fs-extra');
const config = require('config');
const chalk = require('chalk');
const { setupConfig } = require('./lib/config');

// Set up global path references
global.BASE_DIR = __dirname;
global.CONFIG_DIR = path.join(__dirname, 'config');
global.OUTPUT_DIR = path.join(__dirname, config.get('paths.outputDir'));
global.TEMPLATES_DIR = path.join(__dirname, config.get('paths.templatesDir'));
global.SCRIPTS_DIR = path.join(__dirname, config.get('paths.scriptsDir'));
global.LOGS_DIR = path.join(__dirname, config.get('paths.logsDir'));

// Ensure directories exist
fs.ensureDirSync(global.OUTPUT_DIR);
fs.ensureDirSync(global.TEMPLATES_DIR);
fs.ensureDirSync(global.LOGS_DIR);

// Set up CLI
program
  .name('questdb-cli')
  .description('Command-line interface for managing QuestDB databases')
  .version('1.0.0');

// Load all command modules
const commandsDir = path.join(__dirname, 'commands');
fs.readdirSync(commandsDir)
  .filter(file => file.endsWith('.js'))
  .forEach(file => {
    const commandModule = require(path.join(commandsDir, file));
    if (commandModule.registerCommand) {
      commandModule.registerCommand(program);
    }
  });

// Add configuration command
program
  .command('config')
  .description('Manage CLI configuration')
  .option('-l, --list', 'List current configuration')
  .option('-s, --setup', 'Run interactive setup')
  .option('-r, --reset', 'Reset to default configuration')
  .action(async (options) => {
    if (options.list) {
      console.log(chalk.bold('Current configuration:'));
      console.log(JSON.stringify(config, null, 2));
    } else if (options.setup) {
      await setupConfig();
    } else if (options.reset) {
      if (fs.existsSync(path.join(global.CONFIG_DIR, 'local.json'))) {
        fs.unlinkSync(path.join(global.CONFIG_DIR, 'local.json'));
        console.log(chalk.green('Configuration reset to defaults'));
      } else {
        console.log(chalk.yellow('No local configuration to reset'));
      }
    } else {
      program.commands.find(c => c.name() === 'config').help();
    }
  });

// Add help information
program.on('--help', () => {
  console.log('');
  console.log(chalk.bold('Examples:'));
  console.log('  $ questdb-cli query "SELECT * FROM ohlc_1m_v2 LIMIT 10"');
  console.log('  $ questdb-cli table-info "market_data_v2"');
  console.log('  $ questdb-cli export "SELECT * FROM ohlc_1h_v2 WHERE symbol = \'EURUSD\'" --format csv --output eurusd_hourly.csv');
  console.log('');
  console.log(chalk.bold('Documentation:'));
  console.log('  See README.md for detailed usage instructions');
});

// Handle errors
program.exitOverride((err) => {
  if (err.code === 'commander.help') {
    process.exit(0);
  }
  
  console.error(chalk.red(`Error: ${err.message}`));
  process.exit(1);
});

// Parse arguments and run
program.parse(process.argv);

// Show help if no command specified
if (!process.argv.slice(2).length) {
  program.help();
}