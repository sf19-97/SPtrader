# SPtrader Tools Directory

*Created: May 31, 2025*

This directory contains all utilities, scripts, and command-line tools for the SPtrader project.

## Directory Structure

- **`/questdb-cli/`** - Command-line interface for QuestDB management
- **`/devtools-cli/`** - Development utilities for Electron and debugging
- **`/data-feeds/`** - Data ingestion scripts for various providers
- **`/scripts/`** - Utility scripts for database operations and monitoring

## Key Tools

### QuestDB CLI

A command-line interface for managing QuestDB, with features for:
- Querying data
- Monitoring performance
- Managing tables
- Optimizing database operations

```bash
cd ~/SPtrader/tools/questdb-cli
./questdb-cli.sh query "SELECT count(*) FROM market_data_v2"
```

### Data Feeds

Scripts for downloading and ingesting financial data:

```bash
# Load tick data for a symbol and date range
cd ~/SPtrader/tools/data-feeds
python3 dukascopy_loader.py load EURUSD 2023-10-01 2023-10-31

# Run daily data update 
./daily_update.sh
```

### Utility Scripts

Scripts for various system operations:

```bash
# Generate OHLC candles from tick data
cd ~/SPtrader/tools/scripts
python3 production_ohlc_generator.py EURUSD 2023-10-01 2023-10-31

# Monitor OHLC data integrity
python3 monitor_ohlc_integrity.py
```

## Usage Instructions

Each subdirectory contains its own README with specific usage instructions. Most tools can be run from their respective directories or using absolute paths.

For automated tasks, consider using the main CLI:

```bash
cd ~/SPtrader
./sptrader data load EURUSD 2023-10-01 2023-10-31
```