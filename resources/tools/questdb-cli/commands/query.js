/**
 * Query command for QuestDB CLI
 * Executes SQL queries against the database
 */

const chalk = require('chalk');
const path = require('path');
const fs = require('fs-extra');
const { formatTable, formatError, showSuccess } = require('../lib/display');
const { executeQuery, executeHttpQuery, exportData } = require('../lib/database');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('query')
    .description('Execute a SQL query against QuestDB')
    .argument('<sql>', 'SQL query to execute')
    .option('-f, --format <format>', 'Output format (table, json, csv)', 'table')
    .option('-o, --output <filename>', 'Save output to file')
    .option('-l, --limit <limit>', 'Limit number of results', parseInt)
    .option('-p, --protocol <protocol>', 'Protocol to use (pg, http)', 'http')
    .action(async (sql, options) => {
      try {
        // Execute the query
        let result;
        
        if (options.protocol === 'pg') {
          const res = await executeQuery(sql);
          result = res.rows;
        } else {
          const res = await executeHttpQuery(sql);
          
          // Convert QuestDB HTTP format to rows
          if (res.dataset && res.columns) {
            // Extract column names
            const columns = res.columns.map(col => col.name);
            
            // Convert dataset to row objects
            result = res.dataset.map(row => {
              const obj = {};
              columns.forEach((col, i) => {
                obj[col] = row[i];
              });
              return obj;
            });
          } else {
            result = [];
          }
        }
        
        // Apply limit if specified
        if (options.limit && result.length > options.limit) {
          result = result.slice(0, options.limit);
        }
        
        // Output the result
        if (options.output) {
          // Save to file
          const format = options.format === 'table' ? 'json' : options.format;
          const filename = options.output;
          
          const exportResult = await exportData(result, format, filename);
          showSuccess(`Exported ${exportResult.recordCount} records to ${exportResult.path}`);
        } else if (options.format === 'json') {
          // Print as JSON
          console.log(JSON.stringify(result, null, 2));
        } else if (options.format === 'csv') {
          // Print as CSV
          const { Parser } = require('json2csv');
          const fields = result.length > 0 ? Object.keys(result[0]) : [];
          const parser = new Parser({ fields });
          console.log(parser.parse(result));
        } else {
          // Print as table
          console.log(formatTable(result));
        }
        
        // Show result count
        if (!options.output) {
          console.log(chalk.gray(`${result.length} rows returned`));
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