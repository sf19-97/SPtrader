/**
 * Generate OHLC command for QuestDB CLI
 * Creates OHLC candles from tick data
 */

const chalk = require('chalk');
const { formatError, showSuccess, showInfo, showWarning } = require('../lib/display');
const { executeHttpQuery } = require('../lib/database');
const cliProgress = require('cli-progress');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('generate-ohlc')
    .description('Generate OHLC candles from tick data')
    .argument('<symbol>', 'Symbol to generate OHLC for')
    .option('-t, --timeframe <timeframe>', 'Timeframe to generate (1m, 5m, 15m, 30m, 1h, 4h, 1d)', '1m')
    .option('-s, --source <table>', 'Source table for tick data', 'market_data_v2')
    .option('-d, --destination <table>', 'Destination table', '')
    .option('--start <date>', 'Start date (YYYY-MM-DD)')
    .option('--end <date>', 'End date (YYYY-MM-DD)')
    .option('--overwrite', 'Overwrite existing data', false)
    .option('--field <field>', 'Price field to use (bid, ask, price)', 'price')
    .action(async (symbol, options) => {
      try {
        // Validate timeframe
        const validTimeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];
        if (!validTimeframes.includes(options.timeframe)) {
          throw new Error(`Invalid timeframe: ${options.timeframe}. Valid options are: ${validTimeframes.join(', ')}`);
        }
        
        // Determine destination table
        const destTable = options.destination || `ohlc_${options.timeframe}_v2`;
        
        // Check if source table exists and has data
        showInfo(`Checking source table: ${options.source}`);
        const sourceCheckQuery = `
          SELECT COUNT(*) 
          FROM ${options.source} 
          WHERE symbol = '${symbol}'
          ${options.start ? `AND timestamp >= '${options.start}'` : ''}
          ${options.end ? `AND timestamp <= '${options.end}'` : ''}
        `;
        
        const sourceCheck = await executeHttpQuery(sourceCheckQuery);
        const sourceCount = sourceCheck.dataset?.[0]?.[0] || 0;
        
        if (sourceCount === 0) {
          showWarning(`No data found in ${options.source} for symbol ${symbol}`);
          return;
        }
        
        showInfo(`Found ${sourceCount.toLocaleString()} tick records for ${symbol}`);
        
        // Check if destination table exists
        let tableExists = true;
        try {
          await executeHttpQuery(`SELECT * FROM ${destTable} LIMIT 1`);
        } catch (error) {
          tableExists = false;
        }
        
        // Create destination table if it doesn't exist
        if (!tableExists) {
          showInfo(`Creating destination table: ${destTable}`);
          const createTableQuery = `
            CREATE TABLE ${destTable} (
              timestamp TIMESTAMP,
              symbol SYMBOL,
              open DOUBLE,
              high DOUBLE,
              low DOUBLE,
              close DOUBLE,
              volume DOUBLE,
              tick_count LONG,
              vwap DOUBLE,
              trading_session SYMBOL
            ) TIMESTAMP(timestamp) PARTITION BY DAY;
          `;
          
          await executeHttpQuery(createTableQuery);
          showSuccess(`Created table: ${destTable}`);
        }
        
        // Check if there's existing data in the destination table
        if (tableExists && !options.overwrite) {
          const destCheckQuery = `
            SELECT COUNT(*) 
            FROM ${destTable} 
            WHERE symbol = '${symbol}'
            ${options.start ? `AND timestamp >= '${options.start}'` : ''}
            ${options.end ? `AND timestamp <= '${options.end}'` : ''}
          `;
          
          const destCheck = await executeHttpQuery(destCheckQuery);
          const destCount = destCheck.dataset?.[0]?.[0] || 0;
          
          if (destCount > 0) {
            showWarning(`Found ${destCount.toLocaleString()} existing OHLC records for ${symbol}`);
            showWarning(`Use --overwrite to replace existing data`);
            
            // Ask for confirmation
            const inquirer = require('inquirer');
            const confirm = await inquirer.prompt([
              {
                type: 'confirm',
                name: 'proceed',
                message: 'Continue anyway?',
                default: false
              }
            ]);
            
            if (!confirm.proceed) {
              showInfo('Operation cancelled');
              return;
            }
          }
        }
        
        // Determine SAMPLE BY interval based on timeframe
        let sampleInterval;
        switch (options.timeframe) {
          case '1m': sampleInterval = '1m'; break;
          case '5m': sampleInterval = '5m'; break;
          case '15m': sampleInterval = '15m'; break;
          case '30m': sampleInterval = '30m'; break;
          case '1h': sampleInterval = '1h'; break;
          case '4h': sampleInterval = '4h'; break;
          case '1d': sampleInterval = '1d'; break;
          default: sampleInterval = '1m';
        }
        
        // If overwriting, delete existing data first
        if (options.overwrite) {
          const deleteQuery = `
            DELETE FROM ${destTable} 
            WHERE symbol = '${symbol}'
            ${options.start ? `AND timestamp >= '${options.start}'` : ''}
            ${options.end ? `AND timestamp <= '${options.end}'` : ''}
          `;
          
          showInfo(`Deleting existing data for ${symbol}...`);
          await executeHttpQuery(deleteQuery);
        }
        
        // Generate OHLC data
        showInfo(`Generating ${options.timeframe} OHLC candles for ${symbol}...`);
        
        const generateQuery = `
          INSERT INTO ${destTable}
          SELECT 
            timestamp,
            symbol,
            first(${options.field}) as open,
            max(${options.field}) as high,
            min(${options.field}) as low,
            last(${options.field}) as close,
            sum(volume) as volume,
            count() as tick_count,
            avg(${options.field}) as vwap,
            'GENERATED' as trading_session
          FROM ${options.source}
          WHERE symbol = '${symbol}'
          ${options.start ? `AND timestamp >= '${options.start}'` : ''}
          ${options.end ? `AND timestamp <= '${options.end}'` : ''}
          SAMPLE BY ${sampleInterval} ALIGN TO CALENDAR
        `;
        
        await executeHttpQuery(generateQuery);
        
        // Check how many records were generated
        const countQuery = `
          SELECT COUNT(*) 
          FROM ${destTable} 
          WHERE symbol = '${symbol}'
          ${options.start ? `AND timestamp >= '${options.start}'` : ''}
          ${options.end ? `AND timestamp <= '${options.end}'` : ''}
        `;
        
        const countResult = await executeHttpQuery(countQuery);
        const generatedCount = countResult.dataset?.[0]?.[0] || 0;
        
        showSuccess(`Generated ${generatedCount.toLocaleString()} ${options.timeframe} candles for ${symbol}`);
        
        // Show data range
        const rangeQuery = `
          SELECT 
            MIN(timestamp) as min_time,
            MAX(timestamp) as max_time
          FROM ${destTable} 
          WHERE symbol = '${symbol}'
        `;
        
        const rangeResult = await executeHttpQuery(rangeQuery);
        if (rangeResult.dataset && rangeResult.dataset.length > 0) {
          const minTime = rangeResult.dataset[0][0];
          const maxTime = rangeResult.dataset[0][1];
          showInfo(`Data range: ${minTime} to ${maxTime}`);
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