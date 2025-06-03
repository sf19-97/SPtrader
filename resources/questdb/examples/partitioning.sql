-- Partitioning Examples for QuestDB
-- These examples demonstrate effective partitioning strategies for time-series data

-- Basic table with DAY partitioning (default)
CREATE TABLE market_data_day (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Table with MONTH partitioning (for less frequent data)
CREATE TABLE market_data_month (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY MONTH;

-- Table with YEAR partitioning (for sparse data)
CREATE TABLE market_data_year (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY YEAR;

-- No partitioning (not recommended for time-series data)
CREATE TABLE market_data_none (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp);

-- Table with WAL enabled (for real-time data with frequent writes)
CREATE TABLE market_data_wal (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Advanced partitioning with commit lag and uncommitted rows settings
CREATE TABLE market_data_advanced (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) 
  PARTITION BY DAY 
  WITH maxUncommittedRows=10000, commitLag=120000000; -- 2 minute lag

-- Querying data efficiently using partitions
-- (QuestDB uses partitions to optimize these queries)
SELECT * 
FROM market_data_day
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07';
-- This query only scans 7 daily partitions

SELECT * 
FROM market_data_month
WHERE timestamp BETWEEN '2023-01-01' AND '2023-03-31';
-- This query only scans 3 monthly partitions

-- Check partitioning info for a table
SELECT name, partitionBy, maxUncommittedRows, commitLag 
FROM tables() 
WHERE name = 'market_data_day';

-- Get partition count for a table
SELECT name, partitionCount
FROM tables()
WHERE name = 'market_data_day';

-- Managing partitions
-- Add data to specific partitions
INSERT INTO market_data_day(timestamp, symbol, price, volume)
VALUES('2023-01-01T12:00:00.000Z', 'EURUSD', 1.08, 1000);
-- This adds data to the 2023-01-01 partition

-- Dropping specific partitions for data lifecycle management
-- Note: QuestDB doesn't support direct partition dropping
-- Workaround: Create a new table without the partitions you want to drop
CREATE TABLE market_data_day_new AS (
    SELECT * FROM market_data_day
    WHERE timestamp > '2023-01-01'
);
DROP TABLE market_data_day;
RENAME TABLE market_data_day_new TO market_data_day;

-- Best practices for partitioning

-- 1. For high-frequency tick data (millions of rows per day)
CREATE TABLE tick_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    bid DOUBLE,
    ask DOUBLE
) TIMESTAMP(timestamp) 
  PARTITION BY DAY
  WITH maxUncommittedRows=100000; -- Higher value for frequent inserts

-- 2. For daily summary data (one row per day per symbol)
CREATE TABLE daily_summary (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY MONTH;

-- 3. For yearly summary data
CREATE TABLE yearly_summary (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    avg_price DOUBLE,
    total_volume LONG
) TIMESTAMP(timestamp) PARTITION BY YEAR;

-- 4. For real-time data with frequent updates
CREATE TABLE realtime_data (
    timestamp TIMESTAMP,
    sensor_id SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp) 
  PARTITION BY DAY 
  WAL
  WITH maxUncommittedRows=1000, commitLag=30000000; -- 30 second lag

-- 5. For backfill operations (historical data loading)
-- Temporarily increase maxUncommittedRows for faster loading
CREATE TABLE historical_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) 
  PARTITION BY MONTH
  WITH maxUncommittedRows=1000000; -- Very high for batch loading

-- After loading, you might want to reset to normal values:
-- (Not directly supported, requires recreating the table)
CREATE TABLE historical_data_normal AS (
    SELECT * FROM historical_data
);
DROP TABLE historical_data;
RENAME TABLE historical_data_normal TO historical_data;

-- Optimize query performance with partitioning
-- Always specify timestamp range to leverage partitioning
SELECT * 
FROM market_data_day
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-07'
  AND symbol = 'EURUSD';
-- This query will scan only relevant partitions for the date range