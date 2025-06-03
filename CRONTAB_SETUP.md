# SPtrader Automated Data Updates Setup
*Created: May 31, 2025*

## Overview

This guide explains how to set up automatic daily data updates for SPtrader using cron jobs.

## Current Status

✅ **Automated data loading is working!**
- Successfully loaded the latest 3 days of EURUSD data
- Generated OHLC candles for all timeframes
- Configured for daily updates

## Data Summary

- EURUSD data spans from **March 1, 2023** to **May 30, 2025**
- Approximately **20 million** ticks in the database
- Over **150,000** 1-minute candles

## How to Set Up Daily Updates

### 1. Schedule via Crontab

To set up daily updates at 1 AM:

```bash
# Open crontab editor
crontab -e

# Add this line to run daily at 1 AM
0 1 * * * /home/millet_frazier/SPtrader/data_feeds/daily_update.sh
```

### 2. Monitor the Process

Check logs to monitor the update process:

```bash
# View daily update logs
cat /home/millet_frazier/SPtrader/logs/runtime/daily_update.log

# Follow data loader logs in real-time
tail -f /home/millet_frazier/SPtrader/logs/runtime/data_loader.log
```

### 3. Test It Manually

Run the script manually to test:

```bash
# Run daily update script
/home/millet_frazier/SPtrader/data_feeds/daily_update.sh

# Or run for a specific symbol and timeframe
cd /home/millet_frazier/SPtrader/data_feeds
python3 automated_data_loader.py EURUSD 1  # Load last 1 day
```

## Troubleshooting

If updates aren't working:

1. Check if QuestDB is running:
   ```bash
   curl -s "http://localhost:9000/exec?query=SELECT%201;"
   ```

2. Verify ingestion binary exists:
   ```bash
   ls -l /home/millet_frazier/SPtrader/build/ingestion
   ```

3. Check for permission issues:
   ```bash
   chmod +x /home/millet_frazier/SPtrader/data_feeds/daily_update.sh
   ```

4. Review logs for errors:
   ```bash
   cat /home/millet_frazier/SPtrader/logs/runtime/data_loader.log | grep ERROR
   ```

## Adding More Symbols

Edit the daily_update.sh script to add more symbols:

```bash
# Open the script
nano /home/millet_frazier/SPtrader/data_feeds/daily_update.sh

# Modify the symbols loop
for SYMBOL in "EURUSD" "GBPUSD" "USDJPY" "AUDUSD" "USDCAD"; do
  log "🔄 Processing $SYMBOL..."
  python3 automated_data_loader.py "$SYMBOL" 3
done
```