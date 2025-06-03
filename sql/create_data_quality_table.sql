-- Create a data quality tracking table
-- This table will store daily statistics about data quality
-- allowing the system to make intelligent decisions about date ranges

CREATE TABLE IF NOT EXISTS data_quality (
    symbol SYMBOL,
    trading_date TIMESTAMP,
    tick_count LONG,
    first_tick TIMESTAMP,
    last_tick TIMESTAMP,
    hours_coverage INT,
    quality_score DOUBLE,
    quality_rating SYMBOL,
    is_complete BOOLEAN,
    created_at TIMESTAMP
) TIMESTAMP(trading_date) PARTITION BY MONTH;

-- Index for fast lookups
-- QuestDB automatically indexes the designated timestamp column