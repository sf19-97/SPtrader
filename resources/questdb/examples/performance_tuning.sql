-- Performance Tuning Examples for QuestDB
-- These examples demonstrate techniques to optimize QuestDB performance

-- 1. Optimizing Table Design

-- Use SYMBOL type for strings that repeat frequently
CREATE TABLE optimized_market_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,           -- SYMBOL for repeated values like tickers
    exchange SYMBOL,         -- SYMBOL for exchanges (limited set)
    trader_id SYMBOL,        -- SYMBOL for trader IDs (if limited set)
    trader_note VARCHAR,     -- VARCHAR for unique text
    price DOUBLE,            -- DOUBLE for decimal values
    volume LONG              -- LONG for integer values
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Use appropriate timestamp precision (milliseconds)
CREATE TABLE timestamp_optimized (
    timestamp TIMESTAMP(3),  -- Millisecond precision (saves space vs microseconds)
    sensor_id SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- 2. Indexing Strategies

-- SYMBOL columns are indexed automatically
-- Designated TIMESTAMP column is indexed automatically
-- Create index on additional columns only if needed
CREATE TABLE indexed_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,           -- Automatically indexed
    category SYMBOL,         -- Automatically indexed
    user_id LONG,            -- Not indexed by default
    value DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- 3. Query Optimization

-- Filter on designated timestamp first for performance
-- GOOD: timestamp filter first
SELECT * FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
  AND symbol = 'EURUSD';

-- LESS EFFICIENT: non-timestamp filter first
SELECT * FROM market_data
WHERE symbol = 'EURUSD'
  AND timestamp BETWEEN '2023-01-01' AND '2023-01-07';

-- Use LIMIT for testing queries
-- When working with large tables, use LIMIT to test queries quickly
SELECT * FROM market_data
WHERE timestamp > dateadd('d', -30, now())
LIMIT 100;

-- Use explicit JOIN syntax for clarity
-- QuestDB supports limited join types (mainly equi-joins)
SELECT a.timestamp, a.symbol, a.price, b.metadata
FROM market_data a
JOIN symbol_metadata b ON a.symbol = b.symbol
WHERE a.timestamp BETWEEN '2023-01-01' AND '2023-01-07';

-- 4. SAMPLE BY Optimization

-- ALIGN TO CALENDAR for consistent boundaries
SELECT timestamp, symbol, avg(price)
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
SAMPLE BY 1h ALIGN TO CALENDAR;

-- Specify FILL behavior for gaps
SELECT timestamp, symbol, avg(price)
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
SAMPLE BY 1h FILL(NULL);

-- 5. Optimizing Data Import

-- Batch imports for better performance
-- Use COPY for faster data loading from CSV
CREATE TABLE market_data AS (
    SELECT * FROM COPY('/path/to/large_file.csv')
);

-- When importing, specify types for better performance
CREATE TABLE typed_import AS (
    SELECT * FROM COPY('/path/to/data.csv') (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        price DOUBLE,
        volume LONG
    )
);

-- 6. Memory Management

-- Create tables with appropriate commit lag for memory management
CREATE TABLE memory_optimized (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE
) TIMESTAMP(timestamp) 
  PARTITION BY DAY
  WITH maxUncommittedRows=10000, commitLag=120000000; -- 2 minute lag

-- 7. Optimizing LATEST BY Queries

-- For time-series data, use LATEST BY efficiently
-- GOOD: Filter by timestamp range first
SELECT * FROM market_data
WHERE timestamp > dateadd('d', -1, now())
LATEST BY symbol;

-- LESS EFFICIENT: LATEST BY without timestamp filter
SELECT * FROM market_data
LATEST BY symbol;

-- 8. Table Maintenance

-- Check table sizes
SELECT name, size()
FROM tables()
ORDER BY size() DESC;

-- Drop unused tables to free up space
DROP TABLE old_table;

-- Analyze table partition counts
SELECT name, partitionCount
FROM tables()
ORDER BY partitionCount DESC;

-- 9. Query Result Optimization

-- Project only needed columns
-- GOOD: Select only needed columns
SELECT timestamp, symbol, price
FROM market_data
WHERE timestamp > dateadd('d', -1, now());

-- LESS EFFICIENT: Select all columns
SELECT *
FROM market_data
WHERE timestamp > dateadd('d', -1, now());

-- 10. Optimized Count Queries

-- Count efficiently with designated timestamp
SELECT count()
FROM market_data
WHERE timestamp > dateadd('d', -30, now());

-- For unique counts, use grouping
SELECT symbol, count()
FROM market_data
WHERE timestamp > dateadd('d', -30, now())
GROUP BY symbol;

-- 11. Optimize Time Range Queries

-- Break large time ranges into smaller chunks
-- BETTER: Multiple queries with smaller time ranges
-- Query 1:
SELECT * FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07';
-- Query 2:
SELECT * FROM market_data
WHERE timestamp BETWEEN '2023-01-08' AND '2023-01-14';

-- WORSE: One query with very large time range
SELECT * FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-12-31';

-- 12. WAL Mode for Write-Heavy Workloads

-- Enable WAL for tables with frequent updates
CREATE TABLE realtime_data (
    timestamp TIMESTAMP,
    metric SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp) 
  PARTITION BY DAY 
  WAL;

-- Check WAL status of tables
SELECT name, walEnabled
FROM tables();

-- 13. Optimizing for Specific Use Cases

-- Time-based bucketing for visualization
SELECT timestamp, 
       symbol,
       avg(price) AS avg_price,
       min(price) AS min_price,
       max(price) AS max_price
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
  AND symbol = 'EURUSD'
SAMPLE BY 5m ALIGN TO CALENDAR;

-- Efficient cross-symbol comparison
SELECT timestamp,
       sum(CASE WHEN symbol = 'EURUSD' THEN price ELSE 0 END) AS eurusd_price,
       sum(CASE WHEN symbol = 'GBPUSD' THEN price ELSE 0 END) AS gbpusd_price
FROM (
    SELECT timestamp, symbol, last(price) AS price
    FROM market_data
    WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
      AND symbol IN ('EURUSD', 'GBPUSD')
    SAMPLE BY 1h ALIGN TO CALENDAR
);

-- 14. System-Level Optimization

-- These settings would be in questdb.conf
-- cairo.max.file.size.mb=2048         -- Increase max file size
-- cairo.sql.join.metadata.page.size=16777216  -- Increase join buffer
-- cairo.character.store.capacity=1048576  -- For string performance
-- cairo.sql.sort.key.page.size=16777216  -- For ORDER BY performance

-- 15. Monitoring Query Performance

-- Check memory usage
SELECT memory();

-- Get the number of columns for a table
SELECT name, columnCount
FROM tables()
WHERE name = 'market_data';

-- View column details for a table
SELECT * FROM columns('market_data');