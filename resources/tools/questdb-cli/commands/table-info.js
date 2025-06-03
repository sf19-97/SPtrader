/**
 * Table information command for QuestDB CLI
 * Shows details about database tables
 */

const chalk = require('chalk');
const { formatTable, formatError, showInfo } = require('../lib/display');
const { getTableInfo, listTables } = require('../lib/database');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('table-info')
    .description('Get information about database tables')
    .argument('[tableName]', 'Table name (optional)')
    .option('-c, --columns', 'Show column information')
    .option('-s, --stats', 'Show table statistics')
    .option('-a, --all', 'Show all information')
    .action(async (tableName, options) => {
      try {
        // If no table name provided, list all tables
        if (!tableName) {
          const tables = await listTables();
          
          // Format as array of objects for display
          const tableList = tables.map(table => ({
            name: table[0]
          }));
          
          console.log(chalk.bold('Available Tables:'));
          console.log(formatTable(tableList));
          
          showInfo('Use table-info <tableName> to see details for a specific table');
          return;
        }
        
        // Get detailed information for the specified table
        const tableInfo = await getTableInfo(tableName);
        
        if (tableInfo.status === 'not_found') {
          console.error(chalk.red(`Table '${tableName}' does not exist`));
          process.exit(1);
        }
        
        // Display table information
        console.log(chalk.bold(`Table: ${tableName}`));
        
        // Show basic information
        console.log(chalk.gray('Basic Information:'));
        console.log(`  Rows: ${tableInfo.rowCount.toLocaleString()}`);
        
        if (tableInfo.minTimestamp && tableInfo.maxTimestamp) {
          console.log(`  Time Range: ${tableInfo.minTimestamp} to ${tableInfo.maxTimestamp}`);
          
          // Calculate time span
          const start = new Date(tableInfo.minTimestamp);
          const end = new Date(tableInfo.maxTimestamp);
          const days = Math.round((end - start) / (1000 * 60 * 60 * 24));
          console.log(`  Span: ${days} days`);
        }
        
        // Show column information if requested
        if (options.columns || options.all) {
          console.log('');
          console.log(chalk.gray('Columns:'));
          
          const columns = tableInfo.columns.map(col => ({
            name: col[0],
            type: col[1],
            indexed: col[2] === 'true' ? 'Yes' : 'No',
            indexCapacity: col[3]
          }));
          
          console.log(formatTable(columns));
        }
        
        // Show sample data if requested
        if (options.stats || options.all) {
          console.log('');
          console.log(chalk.gray('Sample Data:'));
          
          // Get a few sample rows
          const { executeHttpQuery } = require('../lib/database');
          const sampleQuery = `SELECT * FROM ${tableName} LIMIT 5`;
          const sample = await executeHttpQuery(sampleQuery);
          
          if (sample.dataset && sample.columns) {
            // Extract column names
            const columns = sample.columns.map(col => col.name);
            
            // Convert dataset to row objects
            const rows = sample.dataset.map(row => {
              const obj = {};
              columns.forEach((col, i) => {
                obj[col] = row[i];
              });
              return obj;
            });
            
            console.log(formatTable(rows));
          } else {
            console.log(chalk.yellow('No sample data available'));
          }
        }
      } catch (error) {
        console.error(formatError(error));
        process.exit(1);
      }
    });
}

module.exports = {
  registerCommand
};