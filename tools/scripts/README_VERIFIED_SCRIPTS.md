# Verified Data Pipeline Scripts
*May 31, 2025*

This directory contains the verified data pipeline scripts for SPtrader. These scripts have been created to address the data integrity issues identified in the previous implementation.

## Available Scripts

### 1. verified_ohlc_generator.py

A robust OHLC generator with strict data integrity verification.

**Features:**
- Prevents duplicate candles through DELETE before INSERT
- Verifies high/low bounds against source data
- Checks for inappropriate weekend timestamps
- Validates data at each step of the generation process

**Usage:**
```bash
python3 verified_ohlc_generator.py EURUSD
```

### 2. cleanup_database.py

Prepares the database for fresh OHLC generation by safely backing up and dropping existing OHLC tables.

**Features:**
- Creates timestamped backups of all tables
- Safely drops all OHLC tables
- Preserves raw tick data

**Usage:**
```bash
python3 cleanup_database.py
```

### 3. daily_update_verified.py

A safe replacement for the previous daily update process, using verified scripts.

**Features:**
- Downloads latest data from Dukascopy
- Uses verified OHLC generator
- Processes multiple symbols in sequence
- Detailed logging for troubleshooting

**Usage:**
```bash
python3 daily_update_verified.py EURUSD GBPUSD USDJPY
# Or use default symbols
python3 daily_update_verified.py
```

## Verification Measures

All scripts include the following data integrity measures:

1. **Duplication Prevention:**
   - DELETE before INSERT
   - Explicit GROUP BY validation

2. **Data Validation:**
   - High/low bounds verification
   - Weekend timestamp validation
   - Candle count verification

3. **Error Handling:**
   - Comprehensive error checking
   - Detailed logging
   - Fail-fast behavior on error

## Recommended Workflow

1. **Initial Setup:**
   ```bash
   # Backup and clean database
   python3 cleanup_database.py
   
   # Generate OHLC data for key symbols
   python3 verified_ohlc_generator.py EURUSD
   python3 verified_ohlc_generator.py GBPUSD
   ```

2. **Daily Updates:**
   ```bash
   # Set up in crontab to run daily
   python3 daily_update_verified.py
   ```

3. **Monitoring:**
   - Check logs in `/home/millet_frazier/SPtrader/logs/runtime/`
   - Monitor for any verification failures

## Crontab Setup

To run the daily update automatically:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 1:00 AM
0 1 * * * /home/millet_frazier/SPtrader/scripts/daily_update_verified.py >> /home/millet_frazier/SPtrader/logs/runtime/cron_daily_update.log 2>&1
```