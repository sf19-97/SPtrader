# SPtrader Data Pipeline Rebuild Plan
*May 31, 2025*

## Overview

This document outlines the plan to rebuild the SPtrader data pipeline from scratch after identifying severe data integrity issues in the current implementation.

## Current Status

🚨 **CRITICAL FAILURE**: The current OHLC data pipeline has the following issues:
- Duplicate candles in all OHLC tables
- Data fabrication (candle values inconsistent with source tick data)
- Inconsistent timestamp handling
- No data verification at any stage

## Preserved Components

The following components have been kept as they are still valid:

1. **Raw Data Ingestion**:
   - `dukascopy_importer.py` - Downloads tick data from Dukascopy
   - `dukascopy_to_ilp.py` - Sends data to QuestDB via ILP protocol
   - `dukascopy_to_ilp_batched.py` - Batch version for large datasets

2. **Analysis Tools**:
   - `diagnose_candles.py` - Inspects candles for issues
   - `diagnose_data_coverage.py` - Checks data coverage
   - `verify_timeframe_consistency.py` - Validates timeframe consistency

## Quarantined Components

The following components have been moved to `_DANGEROUS_SCRIPTS_DO_NOT_USE/` directory:

1. **OHLC Generators** (all broken):
   - `simple_ohlc_generator.py` - Creates duplicates
   - `fixed_ohlc_generator.py` - Still creates duplicates
   - `fixed_ohlc_generator_timestamp_fix.py` - Inconsistent fixes
   - Other variants with the same issues

2. **Automated Scripts**:
   - `automated_data_loader.py` - References broken generators
   - `daily_update.sh` - Scheduled job that uses broken scripts

## Rebuild Steps

### 1. Database Cleanup

```sql
-- Preserve raw tick data
CREATE TABLE market_data_v2_preserved AS (SELECT * FROM market_data_v2);

-- Drop all corrupted OHLC tables
DROP TABLE IF EXISTS ohlc_1m_v2;
DROP TABLE IF EXISTS ohlc_5m_v2;
DROP TABLE IF EXISTS ohlc_15m_v2;
DROP TABLE IF EXISTS ohlc_30m_v2;
DROP TABLE IF EXISTS ohlc_1h_v2;
DROP TABLE IF EXISTS ohlc_4h_v2;
DROP TABLE IF EXISTS ohlc_1d_v2;
```

### 2. New OHLC Generator Implementation

Create a new `verified_ohlc_generator.py` script with these key features:

```python
def generate_timeframe(symbol, timeframe, source_table):
    """Generate OHLC data for a specific timeframe with verification"""
    
    # 1. Clear existing data for this symbol
    execute_query(f"DELETE FROM ohlc_{timeframe}_v2 WHERE symbol = '{symbol}'")
    
    # 2. Generate new data
    query = f"""
    INSERT INTO ohlc_{timeframe}_v2
    SELECT 
        timestamp,
        symbol,
        first(price) as open,
        max(price) as high,
        min(price) as low,
        last(price) as close,
        sum(volume) as volume,
        count() as tick_count,
        avg(price) as vwap,
        'AGGREGATED' as trading_session
    FROM {source_table}
    WHERE symbol = '{symbol}'
    SAMPLE BY {timeframe} ALIGN TO CALENDAR
    """
    execute_query(query)
    
    # 3. Verify data integrity
    verify_ohlc_integrity(symbol, timeframe, source_table)
```

### 3. Data Verification Implementation

Implement strict verification at each step:

```python
def verify_ohlc_integrity(symbol, timeframe, source_table):
    """Verify OHLC data integrity against source data"""
    
    # Check for duplicates
    verify_no_duplicates(symbol, timeframe)
    
    # Check high/low against source
    verify_high_low_bounds(symbol, timeframe, source_table)
    
    # Verify weekend handling
    verify_weekend_timestamps(symbol, timeframe)
    
    # Verify candle count matches expectations
    verify_candle_count(symbol, timeframe)
```

### 4. Proper Daily Candle Timestamp Handling

Implement consistent timestamp handling for daily candles:

```python
def generate_daily_candles(symbol):
    """Generate daily candles with proper timestamp handling"""
    
    # 1. Clear existing data
    execute_query(f"DELETE FROM ohlc_1d_v2 WHERE symbol = '{symbol}'")
    
    # 2. Generate with proper timestamp alignment
    query = f"""
    INSERT INTO ohlc_1d_v2
    SELECT 
        timestamp::timestamp - 86400000000 as timestamp,  -- Shift back 1 day
        symbol,
        first(open) as open,
        max(high) as high,
        min(low) as low,
        last(close) as close,
        sum(volume) as volume,
        sum(tick_count) as tick_count,
        avg(vwap) as vwap,
        'AGGREGATED' as trading_session
    FROM ohlc_1h_v2
    WHERE symbol = '{symbol}'
    SAMPLE BY 1d ALIGN TO CALENDAR
    """
    execute_query(query)
    
    # 3. Verify no weekend timestamps (except Sunday market open)
    verify_weekend_timestamps(symbol, "1d")
```

### 5. New Automated Data Pipeline

Create a new automated pipeline with safety measures:

```python
def automated_data_pipeline(symbol, days_back=3):
    """Automated pipeline with verification"""
    
    # 1. Import raw tick data
    import_tick_data(symbol, days_back)
    
    # 2. Generate all timeframes with verification
    for timeframe in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
        if timeframe == "1m":
            generate_timeframe(symbol, timeframe, "market_data_v2")
        elif timeframe == "1d":
            generate_daily_candles(symbol)
        else:
            source = previous_timeframe(timeframe)
            generate_timeframe(symbol, timeframe, f"ohlc_{source}_v2")
        
        # Verify after each step
        verify_integrity_report(symbol, timeframe)
```

### 6. Database Constraints

Add proper constraints to prevent data issues:

```sql
-- Add primary key constraint to prevent duplicates
ALTER TABLE ohlc_1d_v2 ADD CONSTRAINT pk_ohlc_1d_v2 PRIMARY KEY(timestamp, symbol);
```

## Testing Plan

Before putting the new pipeline into production:

1. **Unit Tests**:
   - Test each generation function independently
   - Verify data integrity checks catch errors
   
2. **Integration Tests**:
   - Generate all timeframes and verify consistency
   - Test weekend timestamp handling
   
3. **Verification Scripts**:
   - Create scripts to compare tick data with OHLC data
   - Verify no duplicates exist
   
4. **Monitoring**:
   - Add logging for all database operations
   - Create alerts for data integrity issues

## Deployment Plan

1. **Initial Deployment**:
   - Run new generator on test symbols
   - Verify all integrity checks pass
   
2. **Full Deployment**:
   - Generate OHLC data for all symbols
   - Implement new automated pipeline
   
3. **Monitoring**:
   - Set up daily verification checks
   - Create alerts for any data issues

## Timeline

1. **Phase 1** (Immediate):
   - Database cleanup
   - Basic generator implementation
   
2. **Phase 2** (1-2 days):
   - Full verification implementation
   - Testing framework
   
3. **Phase 3** (2-3 days):
   - New automated pipeline
   - Deployment and monitoring

## Conclusion

This rebuild plan addresses the root causes of the data pipeline failure:

1. **Prevents Duplicates**: Clear existing data + proper constraints
2. **Ensures Data Integrity**: Verification at each step
3. **Consistent Timestamps**: Proper handling of daily candles
4. **Safe Automation**: Verified pipeline with proper error handling

By following this plan, we can rebuild a data pipeline that produces reliable, accurate financial data for the SPtrader application.