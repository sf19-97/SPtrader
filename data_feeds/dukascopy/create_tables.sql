-- Create new tables without USDJPY data
-- Intended for QuestDB direct execution
-- Created: June 1, 2025

-- Create new market_data table
CREATE TABLE market_data_v3 (
    timestamp TIMESTAMP,
    symbol SYMBOL,
    bid DOUBLE,
    ask DOUBLE,
    price DOUBLE,
    spread DOUBLE,
    volume DOUBLE,
    bid_volume DOUBLE,
    ask_volume DOUBLE,
    hour_of_day INT,
    day_of_week INT,
    trading_session SYMBOL,
    market_open BOOLEAN
) timestamp(timestamp) PARTITION BY DAY;

-- Insert only EURUSD data (not USDJPY)
INSERT INTO market_data_v3 
SELECT * FROM market_data_v2 
WHERE symbol != 'USDJPY';

-- Create new OHLC tables without USDJPY
-- 1m
CREATE TABLE ohlc_1m_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_1m_v3
SELECT * FROM ohlc_1m_v2
WHERE symbol != 'USDJPY';

-- 5m
CREATE TABLE ohlc_5m_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_5m_v3
SELECT * FROM ohlc_5m_v2
WHERE symbol != 'USDJPY';

-- 15m
CREATE TABLE ohlc_15m_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_15m_v3
SELECT * FROM ohlc_15m_v2
WHERE symbol != 'USDJPY';

-- 30m
CREATE TABLE ohlc_30m_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_30m_v3
SELECT * FROM ohlc_30m_v2
WHERE symbol != 'USDJPY';

-- 1h
CREATE TABLE ohlc_1h_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_1h_v3
SELECT * FROM ohlc_1h_v2
WHERE symbol != 'USDJPY';

-- 4h
CREATE TABLE ohlc_4h_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_4h_v3
SELECT * FROM ohlc_4h_v2
WHERE symbol != 'USDJPY';

-- 1d
CREATE TABLE ohlc_1d_v3 (
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
) timestamp(timestamp) PARTITION BY DAY;

INSERT INTO ohlc_1d_v3
SELECT * FROM ohlc_1d_v2
WHERE symbol != 'USDJPY';

-- Drop old tables
DROP TABLE market_data_v2;
DROP TABLE ohlc_1m_v2;
DROP TABLE ohlc_5m_v2;
DROP TABLE ohlc_15m_v2;
DROP TABLE ohlc_30m_v2;
DROP TABLE ohlc_1h_v2;
DROP TABLE ohlc_4h_v2;
DROP TABLE ohlc_1d_v2;

-- Rename new tables to original names
RENAME TABLE market_data_v3 TO market_data_v2;
RENAME TABLE ohlc_1m_v3 TO ohlc_1m_v2;
RENAME TABLE ohlc_5m_v3 TO ohlc_5m_v2;
RENAME TABLE ohlc_15m_v3 TO ohlc_15m_v2;
RENAME TABLE ohlc_30m_v3 TO ohlc_30m_v2;
RENAME TABLE ohlc_1h_v3 TO ohlc_1h_v2;
RENAME TABLE ohlc_4h_v3 TO ohlc_4h_v2;
RENAME TABLE ohlc_1d_v3 TO ohlc_1d_v2;