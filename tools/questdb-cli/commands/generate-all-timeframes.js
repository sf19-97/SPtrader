/**
 * Generate All Timeframes command for QuestDB CLI
 * Creates OHLC candles for all timeframes from tick data
 */

const chalk = require('chalk');
const { formatError, showSuccess, showInfo, showWarning, showError } = require('../lib/display');
const { executeHttpQuery } = require('../lib/database');
const cliProgress = require('cli-progress');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('generate-all-timeframes')
    .description('Generate OHLC candles for all timeframes from tick data')
    .argument('<symbol>', 'Symbol to generate OHLC for')
    .option('-s, --source <table>', 'Source table for tick data', 'market_data_v2')
    .option('--start <date>', 'Start date (YYYY-MM-DD)')
    .option('--end <date>', 'End date (YYYY-MM-DD)')
    .option('--verify', 'Verify generated data', false)
    .option('--drop-tables', 'Drop and recreate tables', false)
    .option('--field <field>', 'Price field to use (bid, ask, price)', 'price')
    .action(async (symbol, options) => {
      try {
        // Define all supported timeframes
        const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];
        
        // Format dates for database queries
        let startDate, endDate;
        if (options.start) {
          startDate = new Date(options.start);
          startDate = startDate.toISOString().replace('Z', '');
        }
        
        if (options.end) {
          endDate = new Date(options.end);
          endDate = endDate.toISOString().replace('Z', '');
        }
        
        // Check source table data
        showInfo(`Checking source table: ${options.source}`);
        const sourceCheckQuery = `
          SELECT COUNT(*) 
          FROM ${options.source} 
          WHERE symbol = '${symbol}'
          ${startDate ? `AND timestamp >= '${startDate}'` : ''}
          ${endDate ? `AND timestamp < '${endDate}'` : ''}
        `;
        
        const sourceCheck = await executeHttpQuery(sourceCheckQuery);
        const sourceCount = sourceCheck.dataset?.[0]?.[0] || 0;
        
        if (sourceCount === 0) {
          showError(`No data found in ${options.source} for symbol ${symbol}`);
          return;
        }
        
        showInfo(`Found ${sourceCount.toLocaleString()} tick records for ${symbol}`);
        
        // Drop tables if requested
        if (options.dropTables) {
          showInfo('Dropping existing OHLC tables...');
          for (const tf of timeframes) {
            const dropQuery = `DROP TABLE IF EXISTS ohlc_${tf}_v2`;
            await executeHttpQuery(dropQuery);
          }
        }
        
        // Create tables if they don't exist
        showInfo('Creating OHLC tables...');
        
        // Create tables for all timeframes except daily
        for (const tf of timeframes.filter(tf => tf !== '1d')) {
          const createTableQuery = `
            CREATE TABLE IF NOT EXISTS ohlc_${tf}_v2 (
              timestamp TIMESTAMP,
              symbol SYMBOL,
              open DOUBLE,
              high DOUBLE,
              low DOUBLE,
              close DOUBLE,
              volume DOUBLE,
              tick_count LONG,
              vwap DOUBLE,
              trading_session SYMBOL,
              validation_status SYMBOL
            ) TIMESTAMP(timestamp) PARTITION BY DAY;
          `;
          
          await executeHttpQuery(createTableQuery);
        }
        
        // Create daily table with monthly partitioning
        const createDailyTableQuery = `
          CREATE TABLE IF NOT EXISTS ohlc_1d_v2 (
            timestamp TIMESTAMP,
            symbol SYMBOL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            tick_count LONG,
            vwap DOUBLE,
            trading_session SYMBOL,
            validation_status SYMBOL
          ) TIMESTAMP(timestamp) PARTITION BY MONTH;
        `;
        
        await executeHttpQuery(createDailyTableQuery);
        showSuccess('All OHLC tables created');
        
        // Generate candles for each timeframe
        const progress = new cliProgress.SingleBar({
          format: 'Generating candles |{bar}| {percentage}% | {value}/{total} timeframes',
          barCompleteChar: '█',
          barIncompleteChar: '░',
          hideCursor: true
        }, cliProgress.Presets.shades_classic);
        
        progress.start(timeframes.length, 0);
        
        const results = {};
        for (let i = 0; i < timeframes.length; i++) {
          const tf = timeframes[i];
          
          // Clear existing data for this symbol
          const clearQuery = `
            DELETE FROM ohlc_${tf}_v2 
            WHERE symbol = '${symbol}'
            ${startDate ? `AND timestamp >= '${startDate}'` : ''}
            ${endDate ? `AND timestamp < '${endDate}'` : ''}
          `;
          
          await executeHttpQuery(clearQuery);
          
          // Special handling for daily candles
          let generateQuery;
          if (tf === '1d') {
            generateQuery = `
              INSERT INTO ohlc_${tf}_v2
              SELECT 
                timestamp::timestamp - 86400000000 as timestamp,  -- Shift back 1 day
                symbol,
                first(${options.field}) as open,
                max(${options.field}) as high,
                min(${options.field}) as low,
                last(${options.field}) as close,
                sum(volume) as volume,
                count() as tick_count,
                avg(${options.field}) as vwap,
                'MARKET' as trading_session,
                'VERIFIED' as validation_status
              FROM ${options.source}
              WHERE symbol = '${symbol}'
              ${startDate ? `AND timestamp >= '${startDate}'` : ''}
              ${endDate ? `AND timestamp < '${endDate}'` : ''}
              SAMPLE BY ${tf} ALIGN TO CALENDAR
            `;
          } else {
            generateQuery = `
              INSERT INTO ohlc_${tf}_v2
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
                'MARKET' as trading_session,
                'VERIFIED' as validation_status
              FROM ${options.source}
              WHERE symbol = '${symbol}'
              ${startDate ? `AND timestamp >= '${startDate}'` : ''}
              ${endDate ? `AND timestamp < '${endDate}'` : ''}
              SAMPLE BY ${tf} ALIGN TO CALENDAR
            `;
          }
          
          await executeHttpQuery(generateQuery);
          
          // Count records
          const countQuery = `
            SELECT COUNT(*) 
            FROM ohlc_${tf}_v2 
            WHERE symbol = '${symbol}'
          `;
          
          const countResult = await executeHttpQuery(countQuery);
          const recordCount = countResult.dataset?.[0]?.[0] || 0;
          
          results[tf] = recordCount;
          
          progress.update(i + 1);
        }
        
        progress.stop();
        
        // Show summary
        showSuccess(`\nGeneration complete. Summary:`);
        console.log();
        console.log(chalk.bold(`  Symbol: ${symbol}`));
        console.log(chalk.bold(`  Source: ${sourceCount.toLocaleString()} ticks`));
        console.log(chalk.bold(`  Timeframes:`));
        
        for (const tf of timeframes) {
          console.log(`    ${chalk.cyan(tf.padEnd(3))}: ${results[tf].toLocaleString().padStart(8)} candles`);
        }
        console.log();
        
        // Verify if requested
        if (options.verify) {
          showInfo('Verifying generated OHLC data...');
          
          // Check for duplicate timestamps
          let allValid = true;
          for (const tf of timeframes) {
            // Count total rows
            const countQuery = `SELECT COUNT(*) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
            const countResult = await executeHttpQuery(countQuery);
            
            if (!countResult || !countResult.dataset || !countResult.dataset.length) {
              showError(`Failed to count rows in ${tf}`);
              allValid = false;
              continue;
            }
            
            const totalRows = countResult.dataset[0][0];
            
            // Count distinct timestamps
            const distinctQuery = `SELECT COUNT(DISTINCT timestamp) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
            const distinctResult = await executeHttpQuery(distinctQuery);
            
            if (!distinctResult || !distinctResult.dataset || !distinctResult.dataset.length) {
              showError(`Failed to count distinct timestamps in ${tf}`);
              allValid = false;
              continue;
            }
            
            const distinctTimestamps = distinctResult.dataset[0][0];
            
            if (totalRows !== distinctTimestamps) {
              showError(`Duplicates found in ${tf}: ${totalRows} rows but only ${distinctTimestamps} unique timestamps`);
              allValid = false;
            } else {
              showSuccess(`No duplicates in ${tf} (${distinctTimestamps} unique timestamps)`);
            }
          }
          
          // Weekend checks for daily candles
          if (timeframes.includes('1d')) {
            const weekendQuery = `
              SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
              FROM ohlc_1d_v2
              WHERE symbol = '${symbol}'
              AND EXTRACT(dow FROM timestamp) = 6  -- Saturday
            `;
            
            const weekendResult = await executeHttpQuery(weekendQuery);
            if (weekendResult && weekendResult.dataset && weekendResult.dataset.length > 0) {
              showError(`Found ${weekendResult.dataset.length} Saturday timestamps in daily candles`);
              allValid = false;
            } else {
              showSuccess('No inappropriate weekend timestamps found in daily candles');
            }
          }
          
          // Show verification result
          if (allValid) {
            showSuccess('All verification checks passed');
          } else {
            showError('Some verification checks failed');
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