/**
 * Database utility functions for QuestDB CLI
 */

const { Pool } = require('pg');
const config = require('config');
const fetch = require('node-fetch');
const fs = require('fs-extra');
const path = require('path');
const chalk = require('chalk');

// Database connection pool
let pool = null;

/**
 * Get a database connection pool
 * @returns {Pool} PostgreSQL connection pool
 */
function getPool() {
  if (!pool) {
    const dbConfig = config.get('database');
    
    pool = new Pool({
      host: dbConfig.host,
      port: dbConfig.pgPort,
      user: dbConfig.username,
      password: dbConfig.password,
      database: 'qdb',
      application_name: 'questdb-cli',
      connectionTimeoutMillis: dbConfig.timeout,
      // QuestDB doesn't support prepared statements
      statement_timeout: dbConfig.timeout,
      query_timeout: dbConfig.timeout
    });
    
    // Handle errors
    pool.on('error', (err) => {
      console.error(chalk.red('Unexpected database error:'), err);
      // Don't crash on connection errors, but log them
    });
  }
  
  return pool;
}

/**
 * Execute a SQL query using the PG Wire Protocol
 * @param {string} sql - SQL query to execute
 * @param {Array} params - Query parameters
 * @param {Object} options - Query options
 * @returns {Object} Query result
 */
async function executeQuery(sql, params = [], options = {}) {
  const pool = getPool();
  const client = await pool.connect();
  
  try {
    const result = await client.query(sql, params);
    return result;
  } finally {
    client.release();
  }
}

/**
 * Execute a SQL query using the HTTP API
 * @param {string} sql - SQL query to execute
 * @param {Object} options - Query options
 * @returns {Object} Query result
 */
async function executeHttpQuery(sql, options = {}) {
  const dbConfig = config.get('database');
  const url = `http://${dbConfig.host}:${dbConfig.httpPort}/exec`;
  
  const response = await fetch(`${url}?query=${encodeURIComponent(sql)}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    },
    timeout: dbConfig.timeout
  });
  
  if (!response.ok) {
    throw new Error(`HTTP query failed with status ${response.status}`);
  }
  
  return response.json();
}

/**
 * Send data using ILP protocol
 * @param {Array} records - Array of data records to send
 * @param {string} tableName - Target table name
 * @param {Object} options - ILP options
 */
async function sendIlpData(records, tableName, options = {}) {
  const dbConfig = config.get('database');
  const net = require('net');
  
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    
    client.connect(dbConfig.ilpPort, dbConfig.host, () => {
      // Convert records to ILP format
      let ilpData = '';
      for (const record of records) {
        // Format depends on the table structure
        // This is a basic example for tick data
        if (record.timestamp && record.symbol) {
          const timestamp = typeof record.timestamp === 'object' ? 
            record.timestamp.getTime() * 1000000 : // Convert Date to nanoseconds
            record.timestamp;
            
          const line = `${tableName},symbol=${record.symbol} ` +
            Object.entries(record)
              .filter(([key]) => key !== 'symbol' && key !== 'timestamp')
              .map(([key, value]) => {
                if (typeof value === 'string') {
                  return `${key}="${value}"`;
                }
                return `${key}=${value}`;
              })
              .join(',') +
            ` ${timestamp}\n`;
            
          ilpData += line;
        }
      }
      
      client.write(ilpData);
      client.end();
    });
    
    client.on('close', () => {
      resolve();
    });
    
    client.on('error', (err) => {
      reject(err);
    });
    
    // Set timeout
    client.setTimeout(dbConfig.timeout, () => {
      client.destroy();
      reject(new Error('ILP connection timeout'));
    });
  });
}

/**
 * Get table information
 * @param {string} tableName - Table name
 * @returns {Object} Table information
 */
async function getTableInfo(tableName) {
  // Get column information
  const columnsQuery = `
    SELECT 
      name, 
      type,
      indexed,
      indexBlockCapacity
    FROM table_columns('${tableName}')
  `;
  
  // Get table statistics
  const statsQuery = `
    SELECT 
      COUNT(*) as row_count,
      MIN(timestamp) as min_timestamp,
      MAX(timestamp) as max_timestamp
    FROM ${tableName}
  `;
  
  try {
    const columns = await executeHttpQuery(columnsQuery);
    const stats = await executeHttpQuery(statsQuery);
    
    return {
      name: tableName,
      columns: columns.dataset || [],
      columnCount: columns.count,
      rowCount: stats.dataset?.[0]?.[0] || 0,
      minTimestamp: stats.dataset?.[0]?.[1],
      maxTimestamp: stats.dataset?.[0]?.[2],
      status: 'available'
    };
  } catch (err) {
    if (err.message.includes('table does not exist')) {
      return {
        name: tableName,
        status: 'not_found',
        error: 'Table does not exist'
      };
    }
    throw err;
  }
}

/**
 * List all tables in the database
 * @returns {Array} List of tables
 */
async function listTables() {
  const query = 'SELECT name FROM tables()';
  const result = await executeHttpQuery(query);
  
  return result.dataset || [];
}

/**
 * Export query results to a file
 * @param {Array} data - Query result data
 * @param {string} format - Output format (json, csv, table)
 * @param {string} filename - Output filename
 */
async function exportData(data, format, filename) {
  const outputPath = path.join(global.OUTPUT_DIR, filename);
  
  if (format === 'json') {
    await fs.writeJson(outputPath, data, { spaces: 2 });
  } else if (format === 'csv') {
    const { Parser } = require('json2csv');
    
    // Extract fields from first row if available
    const fields = data.length > 0 ? Object.keys(data[0]) : [];
    const parser = new Parser({ fields });
    const csv = parser.parse(data);
    
    await fs.writeFile(outputPath, csv);
  } else {
    throw new Error(`Unsupported export format: ${format}`);
  }
  
  return {
    path: outputPath,
    recordCount: data.length,
    format
  };
}

// Export functions
module.exports = {
  getPool,
  executeQuery,
  executeHttpQuery,
  sendIlpData,
  getTableInfo,
  listTables,
  exportData
};