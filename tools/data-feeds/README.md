# Dukascopy Data Loader

*Created: May 31, 2025*

A unified tool for loading and managing Dukascopy forex data in SPtrader.

## Quick Start

The loader is now available as a command-line tool:

```bash
# Simple syntax
dukascopy load EURUSD 2023-01-01 2023-01-31

# Daily update with OHLC generation
dukascopy daily --generate-ohlc

# Just generate OHLC from existing data
dukascopy ohlc EURUSD 2023-01-01 2023-01-31

# Verify data integrity
dukascopy verify
```

## Features

- **Unified Interface**: Single tool for all data loading operations
- **Batch Processing**: Handles large date ranges efficiently
- **Resume Capability**: Can resume interrupted downloads
- **OHLC Generation**: Can generate OHLC candles after loading
- **Data Verification**: Verifies data integrity
- **Detailed Logging**: Comprehensive logging to file and console

## Commands

### 1. Loading Data for a Specific Symbol and Date Range

```bash
dukascopy load EURUSD 2023-01-01 2023-01-31 --batch-days 5 --generate-ohlc --verify
```

Arguments:
- `symbol` - Currency pair to load (e.g., EURUSD)
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)
- `--batch-days` - Number of days to process in each batch (default: 3)
- `--generate-ohlc` - Also generate OHLC candles after loading
- `--verify` - Verify data integrity after loading

### 2. Loading Yesterday's Data (Daily Update)

```bash
dukascopy daily --symbols EURUSD GBPUSD --generate-ohlc --verify
```

Arguments:
- `--symbols` - Symbols to load (default: EURUSD GBPUSD USDJPY)
- `--generate-ohlc` - Also generate OHLC candles after loading
- `--verify` - Verify data integrity after loading

### 3. Generating OHLC Candles for Existing Data

```bash
dukascopy ohlc EURUSD 2023-01-01 2023-01-31
```

Arguments:
- `symbol` - Symbol to process (e.g., EURUSD)
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)

### 4. Verifying Data Integrity

```bash
dukascopy verify --symbols EURUSD GBPUSD
```

Arguments:
- `--symbols` - Symbols to verify (default: all symbols)

## Cron Job Setup

To set up a daily cron job:

```bash
# Add to crontab (runs at 1:00 AM daily)
0 1 * * * dukascopy daily --generate-ohlc --verify >> /home/millet_frazier/SPtrader/logs/runtime/daily_cron.log 2>&1
```