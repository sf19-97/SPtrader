# OHLC Candle Generation Guide

*Last Updated: May 31, 2025 13:45 UTC*

## Overview

This guide explains how to generate OHLC (Open-High-Low-Close) candles from tick data for different timeframes in SPtrader.

## Current Status

✅ **Fixed OHLC generation system and rebuilt all candles**
- Successfully implemented direct sampling from tick data for all timeframes
- Fixed issues with QuestDB's SAMPLE BY aggregation
- Implemented proper verification and monitoring
- Added special handling for daily candles to avoid weekend issues

## Raw Data Status

- EURUSD tick data spans from **March 1, 2023** to **May 30, 2025**
- **39,532,411** ticks in the database
- GBPUSD data: 344,893 ticks from Jan 19, 2024 to Jan 25, 2024
- USDJPY data: 691,904 ticks from Jan 19, 2024 to Jan 25, 2024

## OHLC Candle Counts

For a full day of trading:
- 1m: 1,440 candles (60 × 24)
- 5m: 288 candles (12 × 24)
- 15m: 96 candles (4 × 24)
- 30m: 48 candles (2 × 24)
- 1h: 24 candles (1 × 24)
- 4h: 6 candles (24 ÷ 4)
- 1d: 1 candle (1 day)

## How to Generate OHLC Candles

### Direct Generation From Tick Data

The new approach uses direct sampling from tick data for each timeframe, avoiding issues with cascading aggregation.

```bash
# Basic usage
python3 scripts/production_ohlc_generator.py EURUSD

# With specific date range
python3 scripts/production_ohlc_generator.py EURUSD 2023-03-01 2023-03-02
```

### Process Overview

1. **Database Preparation**:
   ```bash
   # Backup existing data
   curl -o backups/market_data_v2_backup.csv "http://localhost:9000/exp?query=SELECT+*+FROM+market_data_v2&fmt=csv"
   ```

2. **OHLC Generation**:
   ```bash
   # Run generator for each symbol
   python3 scripts/production_ohlc_generator.py EURUSD
   python3 scripts/production_ohlc_generator.py GBPUSD
   python3 scripts/production_ohlc_generator.py USDJPY
   ```

3. **Verification**:
   ```bash
   # Verify data integrity
   python3 scripts/production_ohlc_verification.py EURUSD
   ```

### How It Works

The production_ohlc_generator.py script:
1. Creates appropriate table structures for each timeframe
2. Uses QuestDB's SAMPLE BY with ALIGN TO CALENDAR for proper alignment
3. Samples directly from tick data for each timeframe
4. Includes special handling for daily candles to avoid weekend issues
5. Validates and reports candle counts and sample data

## Table Schema

All OHLC tables follow this structure:

```sql
CREATE TABLE ohlc_1h_v2 (
    timestamp TIMESTAMP,       -- Candle timestamp
    symbol SYMBOL,             -- Currency pair
    open DOUBLE,               -- Opening price
    high DOUBLE,               -- Highest price
    low DOUBLE,                -- Lowest price
    close DOUBLE,              -- Closing price
    volume DOUBLE,             -- Volume
    tick_count LONG,           -- Number of ticks in the candle
    vwap DOUBLE,               -- Volume Weighted Average Price
    trading_session SYMBOL,    -- Session marker
    validation_status SYMBOL   -- Validation status
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

Daily tables use `PARTITION BY MONTH` instead.

## Special Handling for Daily Candles

Daily candles require special treatment to align properly with trading days:

```sql
INSERT INTO ohlc_1d_v2
SELECT 
    timestamp::timestamp - 86400000000 as timestamp,  -- Shift back 1 day
    symbol,
    first(price) as open,
    max(price) as high,
    min(price) as low,
    last(price) as close,
    sum(volume) as volume,
    count() as tick_count,
    avg(price) as vwap,
    'MARKET' as trading_session,
    'VERIFIED' as validation_status
FROM market_data_v2
WHERE symbol = 'EURUSD'
AND timestamp >= '2023-03-01T00:00:00.000000Z'
AND timestamp < '2023-03-02T00:00:00.000000Z'
SAMPLE BY 1d ALIGN TO CALENDAR
```

The timestamp shifting ensures proper forex trading day alignment and prevents weekend issues.

## Verification and Monitoring

### Manual Verification

```bash
# Verify a single symbol
python3 scripts/production_ohlc_verification.py EURUSD
```

The verification script checks:
- Candle counts for all timeframes
- No duplicate timestamps
- No inappropriate weekend timestamps
- Price continuity between candles
- Tick coverage quality

### Automated Monitoring

A daily monitoring job runs at 6:00 AM:

```bash
0 6 * * * /home/millet_frazier/SPtrader/scripts/monitor_ohlc_integrity.py
```

This script:
- Checks for new candles
- Verifies no duplicates exist
- Ensures no weekend timestamps in daily candles
- Sends alerts if issues are detected

## Troubleshooting

If you encounter issues:

1. **Check for tick data**:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT COUNT(*) FROM market_data_v2 WHERE symbol='EURUSD'"
   ```

2. **Verify candle counts**:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT COUNT(*) FROM ohlc_1h_v2 WHERE symbol='EURUSD'"
   ```

3. **Check for duplicates**:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT COUNT(*), COUNT(DISTINCT timestamp) FROM ohlc_1h_v2 WHERE symbol='EURUSD'"
   ```

4. **Look for weekend timestamps**:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT * FROM ohlc_1d_v2 WHERE symbol='EURUSD' AND EXTRACT(dow FROM timestamp) = 6"
   ```

## QuestDB Limitations and Workarounds

1. **No DELETE WHERE Clause**:
   - Tables are recreated for each symbol update
   - Non-target data is preserved during regeneration

2. **No HAVING Clause**:
   - COUNT(DISTINCT timestamp) is used for duplicate detection

3. **Limited Window Functions**:
   - Complex window operations are avoided

## Next Steps

1. ✅ Create monitoring system for daily OHLC verification
2. ✅ Implement production-ready generator for all timeframes
3. ✅ Add documentation and production rollout guide
4. ✅ Add the OHLC generator to the daily data loading process
5. Create an integrated API for efficient candle retrieval

---

*This documentation was updated as part of the OHLC data pipeline rebuild project.*