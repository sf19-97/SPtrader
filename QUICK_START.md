# SPtrader - What Actually Works

## Your Working System:

1. **Start Everything:**
   ```bash
   ./sptrader start all
   ```

2. **Open Chart:**
   ```bash
   cd frontend
   ./start-desktop.sh
   ```

3. **Load New Data:**
   ```bash
   cd data_feeds
   python3 dukascopy_to_ilp.py EURUSD 2024-01-01 2024-01-31
   ```

## That's It!

Everything else is noise. The system:
- Downloads forex data from Dukascopy
- Stores it in QuestDB 
- Serves it via Go API
- Shows it in your desktop chart

## Key Commands:
- `sptrader status` - Check if everything's running
- `sptrader logs show` - See what's happening
- `sptrader stop all` - Stop everything

## Current Data:
- EURUSD: Sep 2023 - Mar 2024 (9.5M ticks)
- GBPUSD, USDJPY: Limited data

---
*Everything else in this project is experimental junk from migrations and tests*