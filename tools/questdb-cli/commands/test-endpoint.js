/**
 * Test Endpoint command for QuestDB CLI
 * Tests API endpoints with database data
 */

const chalk = require('chalk');
const fetch = require('node-fetch');
const config = require('config');
const { formatError, showSuccess, showInfo, formatTable } = require('../lib/display');
const { executeHttpQuery } = require('../lib/database');

/**
 * Register the command with the CLI
 * @param {Object} program - Commander program instance
 */
function registerCommand(program) {
  program
    .command('test-endpoint')
    .description('Test API endpoints with database data')
    .argument('<endpoint>', 'API endpoint path (e.g., /api/v1/candles)')
    .option('-p, --params <params>', 'Query parameters (e.g., symbol=EURUSD&tf=1h)')
    .option('-m, --method <method>', 'HTTP method', 'GET')
    .option('-b, --body <body>', 'Request body (for POST/PUT)')
    .option('-c, --compare-query <query>', 'SQL query to compare results with')
    .option('-v, --verbose', 'Show detailed output', false)
    .action(async (endpoint, options) => {
      try {
        // Construct API URL
        const apiConfig = config.get('api');
        const baseUrl = apiConfig.baseUrl;
        const url = `${baseUrl}${endpoint}${options.params ? `?${options.params}` : ''}`;
        
        showInfo(`Testing endpoint: ${options.method} ${url}`);
        
        // Make the API request
        const fetchOptions = {
          method: options.method,
          headers: {
            'Accept': 'application/json'
          },
          timeout: apiConfig.timeout
        };
        
        if (options.body && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
          fetchOptions.headers['Content-Type'] = 'application/json';
          fetchOptions.body = options.body;
        }
        
        const startTime = Date.now();
        const response = await fetch(url, fetchOptions);
        const responseTime = Date.now() - startTime;
        
        // Parse response
        let responseData;
        try {
          responseData = await response.json();
        } catch (error) {
          responseData = { error: 'Failed to parse response as JSON' };
        }
        
        // Display results
        showInfo(`Response time: ${responseTime}ms`);
        showInfo(`Status: ${response.status} ${response.statusText}`);
        
        if (options.verbose) {
          console.log(chalk.gray('Response Headers:'));
          response.headers.forEach((value, key) => {
            console.log(`  ${key}: ${value}`);
          });
        }
        
        // Display response data
        if (responseData) {
          if (options.verbose) {
            console.log(chalk.gray('Response Body:'));
            console.log(JSON.stringify(responseData, null, 2));
          } else {
            // Show summary of response
            const summary = {};
            
            if (Array.isArray(responseData)) {
              summary.count = responseData.length;
              summary.first = responseData[0];
              summary.last = responseData[responseData.length - 1];
            } else if (typeof responseData === 'object') {
              // Extract key metrics
              if (responseData.count !== undefined) summary.count = responseData.count;
              if (responseData.candles !== undefined) summary.candleCount = responseData.candles.length;
              if (responseData.symbol !== undefined) summary.symbol = responseData.symbol;
              if (responseData.timeframe !== undefined) summary.timeframe = responseData.timeframe;
              if (responseData.start !== undefined) summary.start = responseData.start;
              if (responseData.end !== undefined) summary.end = responseData.end;
            }
            
            console.log(chalk.gray('Response Summary:'));
            console.log(JSON.stringify(summary, null, 2));
          }
        }
        
        // Compare with database query if specified
        if (options.compareQuery) {
          showInfo(`Comparing with database query: ${options.compareQuery}`);
          
          const dbResult = await executeHttpQuery(options.compareQuery);
          
          // Convert QuestDB HTTP format to rows
          const columns = dbResult.columns.map(col => col.name);
          const dbRows = dbResult.dataset.map(row => {
            const obj = {};
            columns.forEach((col, i) => {
              obj[col] = row[i];
            });
            return obj;
          });
          
          // Compare row counts
          const apiRowCount = Array.isArray(responseData) ? 
            responseData.length : 
            (responseData.candles ? responseData.candles.length : 0);
            
          showInfo(`API returned ${apiRowCount} records`);
          showInfo(`Database returned ${dbRows.length} records`);
          
          if (apiRowCount !== dbRows.length) {
            showInfo(chalk.yellow(`Row count mismatch: API=${apiRowCount}, DB=${dbRows.length}`));
          } else {
            showSuccess('Row counts match');
          }
          
          // Show sample of database results
          if (dbRows.length > 0 && options.verbose) {
            console.log(chalk.gray('Database Query Results (first 5 rows):'));
            console.log(formatTable(dbRows.slice(0, 5)));
          }
        }
        
        // Show overall result
        if (response.ok) {
          showSuccess(`Endpoint test successful (${responseTime}ms)`);
        } else {
          console.log(chalk.red(`Endpoint test failed with status ${response.status}`));
          if (responseData && responseData.error) {
            console.log(chalk.red(`Error: ${responseData.error}`));
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