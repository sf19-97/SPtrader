-- Purge USDJPY data from all tables
-- Created: 2025-06-01

-- Delete from OHLC tables first
DELETE FROM ohlc_1d_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_4h_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_1h_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_30m_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_15m_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_5m_v2 WHERE symbol='USDJPY';
DELETE FROM ohlc_1m_v2 WHERE symbol='USDJPY';

-- Delete from market data (this will take the longest)
DELETE FROM market_data_v2 WHERE symbol='USDJPY';