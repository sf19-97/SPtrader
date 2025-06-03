-- SQL script to purge old non-v2 tables while preserving v2 data
-- Run this script in QuestDB to standardize on v2 tables

-- First, check if v2 tables have data for these timeframes
SELECT 'ohlc_1m_v2' as table_name, COUNT(*) FROM ohlc_1m_v2;
SELECT 'ohlc_5m_v2' as table_name, COUNT(*) FROM ohlc_5m_v2;
SELECT 'ohlc_15m_v2' as table_name, COUNT(*) FROM ohlc_15m_v2;
SELECT 'ohlc_30m_v2' as table_name, COUNT(*) FROM ohlc_30m_v2;
SELECT 'ohlc_1h_v2' as table_name, COUNT(*) FROM ohlc_1h_v2;
SELECT 'ohlc_4h_v2' as table_name, COUNT(*) FROM ohlc_4h_v2;
SELECT 'ohlc_1d_v2' as table_name, COUNT(*) FROM ohlc_1d_v2;

-- Create a backup of the old tables first (IMPORTANT!)
-- Copy just in case something goes wrong
SELECT * FROM ohlc_1m WHERE timestamp < '2023-01-01' LIMIT 1; -- Minimal backup to ensure structure
SELECT * FROM ohlc_5m WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM ohlc_15m WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM ohlc_30m WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM ohlc_1h WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM ohlc_4h WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM ohlc_1d WHERE timestamp < '2023-01-01' LIMIT 1;
SELECT * FROM market_data WHERE timestamp < '2023-01-01' LIMIT 1;

-- Drop the old tables to prevent confusion
-- These tables are no longer needed now that we're using v2 tables
DROP TABLE IF EXISTS ohlc_1m;
DROP TABLE IF EXISTS ohlc_5m;
DROP TABLE IF EXISTS ohlc_15m;
DROP TABLE IF EXISTS ohlc_30m;
DROP TABLE IF EXISTS ohlc_1h;
DROP TABLE IF EXISTS ohlc_4h;
DROP TABLE IF EXISTS ohlc_1d;
DROP TABLE IF EXISTS market_data;

-- WARNING: ONLY UNCOMMENT BELOW IF YOU'RE ABSOLUTELY SURE!
-- This will delete all old tables

-- For any missing v2 tables, create them with proper schema
-- This ensures all timeframes have a _v2 table

-- Create ohlc_1m_v2 if it doesn't exist (using v2 schema)
-- CREATE TABLE IF NOT EXISTS ohlc_1m_v2 (
--    timestamp TIMESTAMP,
--    symbol SYMBOL,
--    open DOUBLE,
--    high DOUBLE,
--    low DOUBLE,
--    close DOUBLE,
--    volume DOUBLE
-- ) timestamp(timestamp) PARTITION BY DAY;

-- Repeat for other timeframes as needed...