-- OHLC Aggregation Examples for QuestDB
-- These examples show different methods for generating OHLC candles

-- Basic OHLC candle generation (1 minute)
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 1m ALIGN TO CALENDAR;

-- OHLC with filtering by symbol
SELECT 
    timestamp,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM market_data
WHERE symbol = 'EURUSD' AND timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 1m ALIGN TO CALENDAR;

-- Multi-timeframe OHLC generation requires separate queries
-- 5-minute timeframe
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 5m ALIGN TO CALENDAR;

-- Hourly timeframe
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 1h ALIGN TO CALENDAR;

-- Daily timeframe
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(volume) AS volume
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-31'
SAMPLE BY 1d ALIGN TO CALENDAR;

-- OHLC with bid/ask spread calculation
SELECT 
    timestamp,
    symbol,
    first(bid) AS open_bid,
    max(bid) AS high_bid,
    min(bid) AS low_bid,
    last(bid) AS close_bid,
    first(ask) AS open_ask,
    max(ask) AS high_ask,
    min(ask) AS low_ask,
    last(ask) AS close_ask,
    avg(ask - bid) AS avg_spread
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 1h ALIGN TO CALENDAR;

-- OHLC with volume-weighted average price (VWAP)
SELECT 
    timestamp,
    symbol,
    first(price) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price) AS close,
    sum(price * volume) / sum(volume) AS vwap,
    sum(volume) AS volume
FROM market_data
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02'
SAMPLE BY 1h ALIGN TO CALENDAR;

-- IMPORTANT: Cannot generate higher timeframe OHLC from lower timeframe OHLC
-- This will NOT work correctly:
SELECT 
    timestamp,
    first(open) AS open,  -- INCORRECT: will not give true open price
    max(high) AS high,    -- This part is correct
    min(low) AS low,      -- This part is correct
    last(close) AS close  -- INCORRECT: will not give true close price
FROM ohlc_1m
SAMPLE BY 5m ALIGN TO CALENDAR;

-- Must always go back to source data for each timeframe