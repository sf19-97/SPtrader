/**
 * Export command for QuestDB CLI
 * Exports query results to files
 */

const chalk = require('chalk');
const path = require('path');
const fs = require('fs-extra');
const { formatError, showSuccess, showInfo } = require('../lib/display');
const { executeHttpQuery, exportData } = require('../lib/database');
const { Parser } = require('json2csv');
const cliProgress = require('cli-progress');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('export')
    .description('Export query results to a file')
    .argument('<sql>', 'SQL query to execute')
    .requiredOption('-f, --format <format>', 'Output format (json, csv)', 'json')
    .requiredOption('-o, --output <filename>', 'Output filename')
    .option('-b, --batch-size <size>', 'Batch size for large exports', parseInt, 10000)
    .option('--include-headers', 'Include headers in CSV output', true)
    .action(async (sql, options) => {
      try {
        // Create a progress bar
        const progressBar = new cliProgress.SingleBar({
          format: 'Exporting data |{bar}| {percentage}% | {value}/{total} records',
          barCompleteChar: '\u2588',
          barIncompleteChar: '\u2591',
          hideCursor: true
        });
        
        // Start the export process
        showInfo(`Executing query: ${sql}`);
        
        // Get total row count
        const countQuery = `SELECT COUNT(*) FROM (${sql})`;
        const countResult = await executeHttpQuery(countQuery);
        const totalRows = countResult.dataset?.[0]?.[0] || 0;
        
        if (totalRows === 0) {
          showInfo('Query returned no results');
          return;
        }
        
        showInfo(`Found ${totalRows.toLocaleString()} records to export`);
        
        // For large datasets, use batching
        if (totalRows > options.batchSize) {
          const outputPath = path.join(global.OUTPUT_DIR, options.output);
          let processedRows = 0;
          
          // Start progress bar
          progressBar.start(totalRows, 0);
          
          // Prepare output file
          if (options.format === 'json') {
            // Start JSON array
            await fs.writeFile(outputPath, '[\n');
          }
          
          // Process in batches
          let firstBatch = true;
          while (processedRows < totalRows) {
            // Modify query to get next batch
            const batchQuery = `${sql} LIMIT ${options.batchSize} OFFSET ${processedRows}`;
            const result = await executeHttpQuery(batchQuery);
            
            // Convert result to row objects
            const columns = result.columns.map(col => col.name);
            const rows = result.dataset.map(row => {
              const obj = {};
              columns.forEach((col, i) => {
                obj[col] = row[i];
              });
              return obj;
            });
            
            // Write batch to file
            if (options.format === 'json') {
              // Append JSON objects
              const json = rows.map(row => JSON.stringify(row)).join(',\n');
              await fs.appendFile(outputPath, (firstBatch ? '' : ',\n') + json);
            } else if (options.format === 'csv') {
              // Write CSV
              const fields = columns;
              const parser = new Parser({ 
                fields,
                header: firstBatch && options.includeHeaders
              });
              const csv = parser.parse(rows);
              await fs.appendFile(outputPath, (firstBatch ? '' : '\n') + csv);
            }
            
            // Update progress
            processedRows += rows.length;
            progressBar.update(processedRows);
            firstBatch = false;
            
            // Break if no more rows
            if (rows.length < options.batchSize) {
              break;
            }
          }
          
          // Finalize output file
          if (options.format === 'json') {
            // Close JSON array
            await fs.appendFile(outputPath, '\n]');
          }
          
          // Stop progress bar
          progressBar.stop();
          
          showSuccess(`Exported ${processedRows.toLocaleString()} records to ${outputPath}`);
        } else {
          // For smaller datasets, export in one go
          const result = await executeHttpQuery(sql);
          
          // Convert result to row objects
          const columns = result.columns.map(col => col.name);
          const rows = result.dataset.map(row => {
            const obj = {};
            columns.forEach((col, i) => {
              obj[col] = row[i];
            });
            return obj;
          });
          
          // Export data
          const exportResult = await exportData(rows, options.format, options.output);
          showSuccess(`Exported ${exportResult.recordCount.toLocaleString()} records to ${exportResult.path}`);
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