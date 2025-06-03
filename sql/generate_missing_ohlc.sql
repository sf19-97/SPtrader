-- Generate missing OHLC data for higher timeframes (1h, 4h, 1d)
-- This script uses data from market_data_v2 to fill in the missing v2 OHLC tables

-- First ensure that tables exist
-- Create ohlc_1h_v2 if it doesn't already exist
CREATE TABLE IF NOT EXISTS ohlc_1h_v2 (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Create ohlc_4h_v2 if it doesn't already exist
CREATE TABLE IF NOT EXISTS ohlc_4h_v2 (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Create ohlc_1d_v2 if it doesn't already exist
CREATE TABLE IF NOT EXISTS ohlc_1d_v2 (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Generate 1-hour candles from market_data_v2
INSERT INTO ohlc_1h_v2
SELECT 
    timestamp,
    symbol,
    first(bid) as open,
    max(bid) as high,
    min(bid) as low,
    last(bid) as close,
    sum(volume) as volume
FROM market_data_v2
SAMPLE BY 1h ALIGN TO CALENDAR
ORDER BY timestamp;

-- Generate 4-hour candles from market_data_v2
INSERT INTO ohlc_4h_v2
SELECT 
    timestamp,
    symbol,
    first(bid) as open,
    max(bid) as high,
    min(bid) as low,
    last(bid) as close,
    sum(volume) as volume
FROM market_data_v2
SAMPLE BY 4h ALIGN TO CALENDAR
ORDER BY timestamp;

-- Generate daily candles from market_data_v2
INSERT INTO ohlc_1d_v2
SELECT 
    timestamp,
    symbol,
    first(bid) as open,
    max(bid) as high,
    min(bid) as low,
    last(bid) as close,
    sum(volume) as volume
FROM market_data_v2
SAMPLE BY 1d ALIGN TO CALENDAR
ORDER BY timestamp;

-- Verify the generated data
SELECT 'ohlc_1h_v2' as table_name, COUNT(*) FROM ohlc_1h_v2;
SELECT 'ohlc_4h_v2' as table_name, COUNT(*) FROM ohlc_4h_v2;
SELECT 'ohlc_1d_v2' as table_name, COUNT(*) FROM ohlc_1d_v2;

-- Show date ranges for all v2 tables
SELECT 'ohlc_1m_v2' as table_name, min(timestamp) as oldest, max(timestamp) as newest, count(*) as count FROM ohlc_1m_v2;
SELECT 'ohlc_5m_v2' as table_name, min(timestamp) as oldest, max(timestamp) as newest, count(*) as count FROM ohlc_5m_v2;
SELECT 'ohlc_1h_v2' as table_name, min(timestamp) as oldest, max(timestamp) as newest, count(*) as count FROM ohlc_1h_v2;
SELECT 'ohlc_4h_v2' as table_name, min(timestamp) as oldest, max(timestamp) as newest, count(*) as count FROM ohlc_4h_v2;
SELECT 'ohlc_1d_v2' as table_name, min(timestamp) as oldest, max(timestamp) as newest, count(*) as count FROM ohlc_1d_v2;