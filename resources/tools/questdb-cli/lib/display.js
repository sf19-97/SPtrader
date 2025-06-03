/**
 * Display utilities for formatting and presenting data
 */

const chalk = require('chalk');
const { table, getBorderCharacters } = require('table');
const config = require('config');

/**
 * Format a result set as a table
 * @param {Array} data - Array of data objects
 * @param {Object} options - Display options
 * @returns {string} Formatted table
 */
function formatTable(data, options = {}) {
  if (!data || data.length === 0) {
    return chalk.yellow('No data to display');
  }
  
  // Extract display configuration
  const displayConfig = config.get('display');
  const maxWidth = options.maxColumnWidth || displayConfig.maxColumnWidth || 40;
  
  // Extract column headers from the first row
  const headers = Object.keys(data[0]);
  
  // Prepare table data with headers
  const tableData = [
    headers.map(h => chalk.bold(h)) // Header row
  ];
  
  // Add data rows
  for (const row of data) {
    const formattedRow = headers.map(header => {
      const value = row[header];
      
      // Format based on value type
      if (value === null || value === undefined) {
        return chalk.gray('NULL');
      } else if (value instanceof Date) {
        return formatTimestamp(value);
      } else if (typeof value === 'object') {
        return truncateString(JSON.stringify(value), maxWidth);
      } else if (typeof value === 'number') {
        return value.toString();
      } else {
        return truncateString(String(value), maxWidth);
      }
    });
    
    tableData.push(formattedRow);
  }
  
  // Configure table options
  const tableConfig = {
    border: getBorderCharacters('norc'),
    columns: headers.map(header => ({
      width: Math.min(
        Math.max(...tableData.map(row => String(row[headers.indexOf(header)]).length)),
        maxWidth
      )
    })),
    drawHorizontalLine: (index, size) => {
      return index === 0 || index === 1 || index === size;
    }
  };
  
  return table(tableData, tableConfig);
}

/**
 * Format a timestamp according to configuration
 * @param {Date|string|number} timestamp - Timestamp to format
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  
  // Format based on configuration
  const format = config.get('display.timestampFormat');
  
  // Simple formatter - replace with more sophisticated one if needed
  return date.toISOString().replace('T', ' ').slice(0, 23);
}

/**
 * Truncate a string if it exceeds the maximum length
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
function truncateString(str, maxLength) {
  if (!str) return '';
  
  if (str.length <= maxLength) {
    return str;
  }
  
  return str.substring(0, maxLength - 3) + '...';
}

/**
 * Format an error message
 * @param {Error} error - Error object
 * @returns {string} Formatted error message
 */
function formatError(error) {
  if (!error) return '';
  
  let message = chalk.red(`Error: ${error.message || 'Unknown error'}`);
  
  if (error.query) {
    message += '\n' + chalk.gray('Query: ') + error.query;
  }
  
  if (error.code) {
    message += '\n' + chalk.gray('Code: ') + error.code;
  }
  
  return message;
}

/**
 * Display a success message
 * @param {string} message - Success message
 */
function showSuccess(message) {
  console.log(chalk.green(`✓ ${message}`));
}

/**
 * Display a warning message
 * @param {string} message - Warning message
 */
function showWarning(message) {
  console.log(chalk.yellow(`⚠ ${message}`));
}

/**
 * Display an info message
 * @param {string} message - Info message
 */
function showInfo(message) {
  console.log(chalk.blue(`ℹ ${message}`));
}

/**
 * Display an error message
 * @param {string} message - Error message
 */
function showError(message) {
  console.log(chalk.red(`✗ ${message}`));
}

/**
 * Format QuestDB query results
 * @param {Object} results - QuestDB query results
 * @returns {Object} Formatted results
 */
function formatQueryResults(results) {
  if (!results || !results.dataset) {
    return { rows: [], count: 0 };
  }
  
  const columns = results.columns || [];
  const dataset = results.dataset || [];
  
  // Convert dataset to rows with named properties
  const rows = dataset.map(row => {
    const obj = {};
    columns.forEach((col, i) => {
      obj[col.name] = row[i];
    });
    return obj;
  });
  
  return {
    rows,
    count: rows.length,
    truncated: results.truncated
  };
}

/**
 * Print QuestDB query results
 * @param {Object} results - QuestDB query results
 * @param {Object} options - Display options
 */
function printQueryResults(results, options = {}) {
  if (!results || !results.dataset) {
    showInfo('No results returned');
    return;
  }
  
  const format = options.format || config.get('defaults.format');
  const { rows, count, truncated } = formatQueryResults(results);
  
  if (count === 0) {
    showInfo('Query returned zero rows');
    return;
  }
  
  if (format === 'table') {
    console.log(formatTable(rows));
  } else if (format === 'json') {
    console.log(JSON.stringify(rows, null, 2));
  } else if (format === 'csv') {
    const { Parser } = require('json2csv');
    const fields = Object.keys(rows[0]);
    const parser = new Parser({ fields });
    console.log(parser.parse(rows));
  }
  
  if (truncated) {
    showWarning('Results were truncated. Use --limit or export to file for complete results.');
  }
  
  showInfo(`${count} row${count !== 1 ? 's' : ''} returned`);
}

module.exports = {
  formatTable,
  formatTimestamp,
  truncateString,
  formatError,
  showSuccess,
  showWarning,
  showInfo,
  showError,
  formatQueryResults,
  printQueryResults
};