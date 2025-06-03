/**
 * Verify OHLC command for QuestDB CLI
 * Validates OHLC data integrity
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
    .command('verify-ohlc')
    .description('Verify OHLC data integrity')
    .argument('<symbol>', 'Symbol to verify')
    .option('-t, --timeframes <timeframes>', 'Comma-separated list of timeframes to verify (1m,5m,15m,30m,1h,4h,1d)', '1m,5m,15m,30m,1h,4h,1d')
    .option('--detailed', 'Show detailed verification results', false)
    .option('--report <file>', 'Save verification report to file')
    .action(async (symbol, options) => {
      try {
        // Parse timeframes
        const timeframes = options.timeframes.split(',').map(tf => tf.trim());
        
        // Validate timeframes
        const validTimeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];
        for (const tf of timeframes) {
          if (!validTimeframes.includes(tf)) {
            throw new Error(`Invalid timeframe: ${tf}. Valid options are: ${validTimeframes.join(', ')}`);
          }
        }
        
        // Initialize report
        const report = {
          symbol,
          timestamp: new Date().toISOString(),
          timeframes: {},
          summary: {
            passed: true,
            warnings: 0,
            errors: 0
          }
        };
        
        // Verify each timeframe
        for (const tf of timeframes) {
          showInfo(`Verifying ${tf} data for ${symbol}...`);
          
          // Initialize timeframe report
          report.timeframes[tf] = {
            checks: {},
            passed: true,
            warnings: 0,
            errors: 0
          };
          
          // Check 1: Count candles
          try {
            const countQuery = `SELECT COUNT(*) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
            const countResult = await executeHttpQuery(countQuery);
            const count = countResult.dataset?.[0]?.[0] || 0;
            
            report.timeframes[tf].checks.candleCount = {
              name: 'Candle Count',
              count,
              passed: count > 0,
              message: count > 0 ? `Found ${count} candles` : 'No candles found'
            };
            
            if (count === 0) {
              showError(`No ${tf} candles found for ${symbol}`);
              report.timeframes[tf].passed = false;
              report.timeframes[tf].errors++;
              report.summary.passed = false;
              report.summary.errors++;
            } else {
              showSuccess(`Found ${count} ${tf} candles`);
            }
          } catch (error) {
            showError(`Failed to check candle count: ${error.message}`);
            report.timeframes[tf].checks.candleCount = {
              name: 'Candle Count',
              passed: false,
              error: error.message
            };
            report.timeframes[tf].passed = false;
            report.timeframes[tf].errors++;
            report.summary.passed = false;
            report.summary.errors++;
          }
          
          // Check 2: Verify no duplicates
          try {
            // Count total rows
            const countQuery = `SELECT COUNT(*) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
            const countResult = await executeHttpQuery(countQuery);
            const totalRows = countResult.dataset?.[0]?.[0] || 0;
            
            // Count distinct timestamps
            const distinctQuery = `SELECT COUNT(DISTINCT timestamp) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
            const distinctResult = await executeHttpQuery(distinctQuery);
            const distinctTimestamps = distinctResult.dataset?.[0]?.[0] || 0;
            
            const hasDuplicates = totalRows !== distinctTimestamps;
            
            report.timeframes[tf].checks.duplicates = {
              name: 'Duplicate Check',
              totalRows,
              distinctTimestamps,
              passed: !hasDuplicates,
              message: hasDuplicates 
                ? `Found duplicates: ${totalRows} rows but only ${distinctTimestamps} unique timestamps` 
                : `No duplicates (${distinctTimestamps} unique timestamps)`
            };
            
            if (hasDuplicates) {
              showError(`Duplicates found in ${tf}: ${totalRows} rows but only ${distinctTimestamps} unique timestamps`);
              report.timeframes[tf].passed = false;
              report.timeframes[tf].errors++;
              report.summary.passed = false;
              report.summary.errors++;
            } else {
              showSuccess(`No duplicates in ${tf} (${distinctTimestamps} unique timestamps)`);
            }
          } catch (error) {
            showError(`Failed to check duplicates: ${error.message}`);
            report.timeframes[tf].checks.duplicates = {
              name: 'Duplicate Check',
              passed: false,
              error: error.message
            };
            report.timeframes[tf].passed = false;
            report.timeframes[tf].errors++;
            report.summary.passed = false;
            report.summary.errors++;
          }
          
          // Check 3: Weekend timestamps (only for daily candles)
          if (tf === '1d') {
            try {
              // Check for Saturday timestamps
              const saturdayQuery = `
                SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
                FROM ohlc_1d_v2
                WHERE symbol = '${symbol}'
                AND EXTRACT(dow FROM timestamp) = 6  -- Saturday
              `;
              
              const saturdayResult = await executeHttpQuery(saturdayQuery);
              const saturdayTimestamps = saturdayResult.dataset?.length || 0;
              
              // Check for early Sunday timestamps
              const sundayQuery = `
                SELECT timestamp, EXTRACT(dow FROM timestamp) as day_of_week
                FROM ohlc_1d_v2
                WHERE symbol = '${symbol}'
                AND EXTRACT(dow FROM timestamp) = 0  -- Sunday
                AND EXTRACT(hour FROM timestamp) < 22  -- Before 22:00 UTC (typical market open)
              `;
              
              const sundayResult = await executeHttpQuery(sundayQuery);
              const sundayTimestamps = sundayResult.dataset?.length || 0;
              
              const hasWeekendIssues = saturdayTimestamps > 0 || sundayTimestamps > 0;
              
              report.timeframes[tf].checks.weekendTimestamps = {
                name: 'Weekend Timestamps',
                saturdayTimestamps,
                sundayTimestamps,
                passed: !hasWeekendIssues,
                message: hasWeekendIssues
                  ? `Found weekend issues: ${saturdayTimestamps} Saturday timestamps, ${sundayTimestamps} early Sunday timestamps`
                  : 'No inappropriate weekend timestamps'
              };
              
              if (hasWeekendIssues) {
                showError(`Weekend issues found in ${tf}: ${saturdayTimestamps} Saturday timestamps, ${sundayTimestamps} early Sunday timestamps`);
                report.timeframes[tf].passed = false;
                report.timeframes[tf].errors++;
                report.summary.passed = false;
                report.summary.errors++;
              } else {
                showSuccess(`No inappropriate weekend timestamps in ${tf}`);
              }
            } catch (error) {
              showError(`Failed to check weekend timestamps: ${error.message}`);
              report.timeframes[tf].checks.weekendTimestamps = {
                name: 'Weekend Timestamps',
                passed: false,
                error: error.message
              };
              report.timeframes[tf].passed = false;
              report.timeframes[tf].errors++;
              report.summary.passed = false;
              report.summary.errors++;
            }
          }
          
          // Check 4: Price continuity
          try {
            const continuityQuery = `
              SELECT 
                timestamp, 
                close,
                lead(open) OVER (ORDER BY timestamp) AS next_open,
                abs(close - lead(open) OVER (ORDER BY timestamp)) AS price_gap
              FROM ohlc_${tf}_v2
              WHERE symbol = '${symbol}'
              ORDER BY timestamp
            `;
            
            const continuityResult = await executeHttpQuery(continuityQuery);
            const largeGaps = [];
            
            if (continuityResult.dataset) {
              for (const row of continuityResult.dataset) {
                if (row.length >= 4 && row[3] !== null && row[3] > 0.0010) { // 10 pips gap
                  largeGaps.push({
                    timestamp: row[0],
                    close: row[1],
                    nextOpen: row[2],
                    gap: row[3]
                  });
                }
              }
            }
            
            const hasLargeGaps = largeGaps.length > 0;
            
            report.timeframes[tf].checks.priceContinuity = {
              name: 'Price Continuity',
              largeGapCount: largeGaps.length,
              passed: true, // Not a failure, just a warning
              warning: hasLargeGaps,
              largeGaps: options.detailed ? largeGaps : undefined,
              message: hasLargeGaps
                ? `Found ${largeGaps.length} large price gaps`
                : 'Price continuity verified'
            };
            
            if (hasLargeGaps) {
              showWarning(`Found ${largeGaps.length} large price gaps in ${tf}`);
              report.timeframes[tf].warnings++;
              report.summary.warnings++;
            } else {
              showSuccess(`Price continuity verified in ${tf}`);
            }
          } catch (error) {
            showError(`Failed to check price continuity: ${error.message}`);
            report.timeframes[tf].checks.priceContinuity = {
              name: 'Price Continuity',
              passed: false,
              error: error.message
            };
            report.timeframes[tf].passed = false;
            report.timeframes[tf].errors++;
            report.summary.passed = false;
            report.summary.errors++;
          }
          
          // Check 5: Tick coverage (only for 1m)
          if (tf === '1m') {
            try {
              const coverageQuery = `
                SELECT timestamp, tick_count, high, low, high - low AS range
                FROM ohlc_1m_v2
                WHERE symbol = '${symbol}'
                AND tick_count < 5
                AND high - low > 0.0010  -- 10 pips range
                LIMIT 20
              `;
              
              const coverageResult = await executeHttpQuery(coverageQuery);
              const suspiciousCandles = coverageResult.dataset || [];
              
              const hasCoverageIssues = suspiciousCandles.length > 0;
              
              report.timeframes[tf].checks.tickCoverage = {
                name: 'Tick Coverage',
                suspiciousCount: suspiciousCandles.length,
                passed: true, // Not a failure, just a warning
                warning: hasCoverageIssues,
                suspiciousCandles: options.detailed ? suspiciousCandles : undefined,
                message: hasCoverageIssues
                  ? `Found ${suspiciousCandles.length} candles with suspicious tick coverage`
                  : 'Tick coverage verified'
              };
              
              if (hasCoverageIssues) {
                showWarning(`Found ${suspiciousCandles.length} candles with suspicious tick coverage in ${tf}`);
                report.timeframes[tf].warnings++;
                report.summary.warnings++;
              } else {
                showSuccess(`Tick coverage verified in ${tf}`);
              }
            } catch (error) {
              showError(`Failed to check tick coverage: ${error.message}`);
              report.timeframes[tf].checks.tickCoverage = {
                name: 'Tick Coverage',
                passed: false,
                error: error.message
              };
              // Not marking as failed since this is just a warning
              report.timeframes[tf].warnings++;
              report.summary.warnings++;
            }
          }
          
          // Check 6: Verify timeframe ratios (only when verifying all timeframes)
          if (timeframes.length === validTimeframes.length && timeframes.includes('1m') && timeframes.includes('1d')) {
            try {
              const counts = {};
              
              // Get counts for all timeframes
              for (const tf of timeframes) {
                const countQuery = `SELECT COUNT(*) FROM ohlc_${tf}_v2 WHERE symbol = '${symbol}'`;
                const countResult = await executeHttpQuery(countQuery);
                counts[tf] = countResult.dataset?.[0]?.[0] || 0;
              }
              
              // Check ratios between timeframes
              const ratioChecks = [
                { from: '1m', to: '5m', minRatio: 4.5, ratio: counts['1m'] / counts['5m'] },
                { from: '5m', to: '15m', minRatio: 2.5, ratio: counts['5m'] / counts['15m'] },
                { from: '15m', to: '30m', minRatio: 1.5, ratio: counts['15m'] / counts['30m'] },
                { from: '30m', to: '1h', minRatio: 1.5, ratio: counts['30m'] / counts['1h'] },
                { from: '1h', to: '4h', minRatio: 3.5, ratio: counts['1h'] / counts['4h'] },
                { from: '4h', to: '1d', minRatio: 3.5, ratio: counts['4h'] / counts['1d'] }
              ];
              
              const failedRatios = ratioChecks.filter(check => check.ratio < check.minRatio);
              
              report.timeframes.ratios = {
                name: 'Timeframe Ratios',
                checks: ratioChecks,
                passed: failedRatios.length === 0,
                failedRatios,
                message: failedRatios.length === 0
                  ? 'All timeframe ratios are correct'
                  : `${failedRatios.length} timeframe ratios are incorrect`
              };
              
              if (failedRatios.length > 0) {
                showError(`Timeframe ratio issues found:`);
                for (const failure of failedRatios) {
                  showError(`  ${failure.from} to ${failure.to}: ratio is ${failure.ratio.toFixed(2)} (expected >= ${failure.minRatio})`);
                }
                report.summary.passed = false;
                report.summary.errors++;
              } else {
                showSuccess('All timeframe ratios are correct');
              }
            } catch (error) {
              showError(`Failed to check timeframe ratios: ${error.message}`);
              report.timeframes.ratios = {
                name: 'Timeframe Ratios',
                passed: false,
                error: error.message
              };
              report.summary.passed = false;
              report.summary.errors++;
            }
          }
        }
        
        // Display summary
        console.log();
        console.log(chalk.bold(`Verification Summary for ${symbol}:`));
        console.log();
        
        if (report.summary.passed && report.summary.warnings === 0) {
          console.log(chalk.green('✓ All checks passed with no warnings'));
        } else if (report.summary.passed) {
          console.log(chalk.yellow(`✓ All checks passed with ${report.summary.warnings} warnings`));
        } else {
          console.log(chalk.red(`✗ Verification failed with ${report.summary.errors} errors, ${report.summary.warnings} warnings`));
        }
        
        // Save report if requested
        if (options.report) {
          const fs = require('fs-extra');
          const path = require('path');
          const reportPath = path.join(global.OUTPUT_DIR, options.report);
          
          await fs.writeJson(reportPath, report, { spaces: 2 });
          showInfo(`Verification report saved to ${reportPath}`);
        }
        
        // Exit with appropriate code
        if (!report.summary.passed) {
          process.exit(1);
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