-- QuestDB Optimization Script for Viewport Queries
-- This creates pre-aggregated tables for different zoom levels

-- 1 hour aggregation for medium zoom
DROP TABLE IF EXISTS ohlc_1h_viewport;
CREATE TABLE ohlc_1h_viewport AS (
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        count(*) as tick_count
    FROM ohlc_5m_v2
    SAMPLE BY 1h ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY WEEK;

-- 4 hour aggregation for wide zoom  
DROP TABLE IF EXISTS ohlc_4h_viewport;
CREATE TABLE ohlc_4h_viewport AS (
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        count(*) as tick_count
    FROM ohlc_5m_v2
    SAMPLE BY 4h ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY MONTH;

-- Daily aggregation for year views
DROP TABLE IF EXISTS ohlc_1d_viewport;
CREATE TABLE ohlc_1d_viewport AS (
    SELECT 
        timestamp,
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        count(*) as tick_count
    FROM ohlc_1h_v2
    SAMPLE BY 1d ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY YEAR;

-- Create fast lookup tables for v1 data (Oanda)
DROP TABLE IF EXISTS eurusd_1h_viewport_oanda;
CREATE TABLE eurusd_1h_viewport_oanda AS (
    SELECT 
        timestamp,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume
    FROM eurusd_5m_oanda
    SAMPLE BY 1h ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY WEEK;

DROP TABLE IF EXISTS eurusd_4h_viewport_oanda;
CREATE TABLE eurusd_4h_viewport_oanda AS (
    SELECT 
        timestamp,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume
    FROM eurusd_5m_oanda
    SAMPLE BY 4h ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY MONTH;

DROP TABLE IF EXISTS eurusd_1d_viewport_oanda;
CREATE TABLE eurusd_1d_viewport_oanda AS (
    SELECT 
        timestamp,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume
    FROM eurusd_1h_oanda
    SAMPLE BY 1d ALIGN TO CALENDAR
) timestamp(timestamp) PARTITION BY YEAR;

-- Verify tables
SELECT table, partition_by, row_count 
FROM tables 
WHERE table LIKE '%viewport%';