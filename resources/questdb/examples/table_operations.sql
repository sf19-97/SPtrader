-- Table Operations Examples for QuestDB
-- These examples show common table management operations

-- Create table with designated timestamp
CREATE TABLE market_data (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    bid DOUBLE,
    ask DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Create table with millisecond precision timestamp
CREATE TABLE high_frequency_data (
    timestamp TIMESTAMP(3),  -- Millisecond precision
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Create table from SELECT query
CREATE TABLE ohlc_daily AS (
    SELECT 
        timestamp,
        symbol,
        first(price) AS open,
        max(price) AS high,
        min(price) AS low,
        last(price) AS close,
        sum(volume) AS volume
    FROM market_data
    SAMPLE BY 1d ALIGN TO CALENDAR
);

-- Add column to existing table
ALTER TABLE market_data ADD COLUMN spread DOUBLE;

-- Drop column from table (not supported in QuestDB)
-- Workaround: Create new table without the column
CREATE TABLE market_data_new AS (
    SELECT 
        timestamp,
        symbol,
        bid,
        ask,
        volume
        -- Exclude 'spread' column
    FROM market_data
);
DROP TABLE market_data;
RENAME TABLE market_data_new TO market_data;

-- Rename table
RENAME TABLE old_table_name TO new_table_name;

-- Drop table
DROP TABLE table_name;

-- "Delete" data from table (not directly supported)
-- Workaround: Create new table with filtered data
CREATE TABLE market_data_filtered AS (
    SELECT * FROM market_data
    WHERE timestamp > '2023-01-01'
);
DROP TABLE market_data;
RENAME TABLE market_data_filtered TO market_data;

-- "Update" data in table (not directly supported)
-- Workaround: Create new table with updated values
CREATE TABLE market_data_updated AS (
    SELECT
        timestamp,
        symbol,
        -- Conditional value replacement
        CASE 
            WHEN symbol = 'EURUSD' AND timestamp BETWEEN '2023-01-01' AND '2023-01-02' 
            THEN bid * 1.001 
            ELSE bid 
        END AS bid,
        ask,
        volume
    FROM market_data
);
DROP TABLE market_data;
RENAME TABLE market_data_updated TO market_data;

-- Table optimization: rebuild table with optimal settings
CREATE TABLE market_data_optimized AS (
    SELECT * FROM market_data
);
DROP TABLE market_data;
RENAME TABLE market_data_optimized TO market_data;

-- Data retention policy implementation
-- Keep only last 90 days of data
CREATE TABLE market_data_retained AS (
    SELECT * FROM market_data
    WHERE timestamp > dateadd('d', -90, now())
);
DROP TABLE market_data;
RENAME TABLE market_data_retained TO market_data;

-- Create table with value-based partitioning
CREATE TABLE market_data_by_symbol (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    price DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY DAY
  WITH maxUncommittedRows=10000, commitLag=120000000;

-- Create table with WAL enabled (better for frequent writes)
CREATE TABLE real_time_data (
    timestamp TIMESTAMP,
    sensor_id SYMBOL,
    value DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Get information about tables
SELECT name, designatedTimestamp FROM tables();