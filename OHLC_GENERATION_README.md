# OHLC Candle Generation Guide

*Last Updated: May 31, 2025*

## Overview

This guide explains how to generate OHLC (Open-High-Low-Close) candles from tick data for different timeframes in SPtrader.

## Current Status

✅ **Fixed OHLC generation system and rebuilt all candles**
- Successfully generated 1-minute candles directly from all tick data (March 2023 - May 2025)
- Generated higher timeframes (5m, 15m, 30m, 1h, 4h, 1d) from 1-minute data
- Fixed issues with QuestDB's SAMPLE BY aggregation

## Raw Data Status

- EURUSD tick data spans from **March 1, 2023** to **May 30, 2025**
- **39,519,525** ticks in the database
- **No gaps** in the data

## OHLC Candle Counts

Current OHLC candle counts for EURUSD:
- 1m: 585,940 candles
- 5m: 117,802 candles
- 15m: 39,279 candles
- 30m: 19,641 candles
- 1h: 9,821 candles
- 4h: 2,676 candles
- 1d: 667 candles

All candles span the full date range from **March 1, 2023** to **May 30, 2025**.

## How to Generate OHLC Candles

### Step 1: Generate 1-minute Candles From Tick Data

```python
# Connect to QuestDB
import requests

# Create a new table
requests.get('http://localhost:9000/exec', params={'query': 'DROP TABLE IF EXISTS ohlc_1m_v2_new'})
requests.get('http://localhost:9000/exec', params={'query': """
CREATE TABLE ohlc_1m_v2_new (
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
) TIMESTAMP(timestamp) PARTITION BY DAY;
"""})

# Generate 1-minute candles from tick data
tick_query = """
INSERT INTO ohlc_1m_v2_new
SELECT 
    timestamp,
    symbol,
    first(bid) as open,
    max(bid) as high,
    min(bid) as low,
    last(bid) as close,
    sum(volume) as volume,
    count() as tick_count,
    avg(bid) as vwap,
    'MARKET' as trading_session
FROM market_data_v2
WHERE symbol = 'EURUSD'
SAMPLE BY 1m ALIGN TO CALENDAR
"""
requests.get('http://localhost:9000/exec', params={'query': tick_query})

# Swap tables
requests.get('http://localhost:9000/exec', params={'query': 'DROP TABLE IF EXISTS ohlc_1m_v2_old'})
requests.get('http://localhost:9000/exec', params={'query': 'RENAME TABLE ohlc_1m_v2 TO ohlc_1m_v2_old'})
requests.get('http://localhost:9000/exec', params={'query': 'RENAME TABLE ohlc_1m_v2_new TO ohlc_1m_v2'})
```

### Step 2: Generate Higher Timeframes

Use the `simple_ohlc_generator.py` script:

```bash
cd /home/millet_frazier/SPtrader/scripts
python3 simple_ohlc_generator.py EURUSD
```

This script:
1. Uses 1-minute candles as the source
2. Directly generates all higher timeframes
3. Preserves existing data for other symbols
4. Uses QuestDB's SAMPLE BY feature with proper alignment

## Troubleshooting

If you encounter issues with OHLC generation:

1. Check for 1-minute candles first:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT COUNT(*) FROM ohlc_1m_v2 WHERE symbol='EURUSD'"
   ```

2. Make sure QuestDB is running:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SELECT 1"
   ```

3. Check if tables have the correct schema:
   ```bash
   curl -G 'http://localhost:9000/exec' --data-urlencode "query=SHOW COLUMNS FROM ohlc_15m_v2"
   ```

4. Check for data gaps:
   ```bash
   cd /home/millet_frazier/SPtrader/tools
   python3 check_data_gaps.py EURUSD --ohlc
   ```

## Key Insights

1. **QuestDB SAMPLE BY Syntax**: Works best directly on 1-minute candles
2. **Atomic Table Swapping**: Safer than TRUNCATE for table replacement
3. **Performance**: Generating OHLC candles directly from tick data is efficient with QuestDB

## Next Steps

1. Add automated OHLC generation to the daily data loading process
2. Create a unified candle generation script that works with all symbols
3. Implement periodic OHLC verification to catch any data issues