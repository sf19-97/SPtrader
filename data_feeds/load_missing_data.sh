#!/bin/bash
# Load missing EURUSD data for Oct-Dec 2023
# Created: May 27, 2025

echo "Loading missing EURUSD data in batches..."
echo "This will load October, November, and December 2023"
echo ""

# Load October 2023
echo "📅 Loading October 2023..."
python3 /home/millet_frazier/SPtrader/data_feeds/dukascopy_to_ilp_batched.py EURUSD 2023-10-01 2023-10-31

# Load November 2023
echo -e "\n📅 Loading November 2023..."
python3 /home/millet_frazier/SPtrader/data_feeds/dukascopy_to_ilp_batched.py EURUSD 2023-11-01 2023-11-30

# Load December 2023
echo -e "\n📅 Loading December 2023..."
python3 /home/millet_frazier/SPtrader/data_feeds/dukascopy_to_ilp_batched.py EURUSD 2023-12-01 2023-12-31

echo -e "\n✅ Done! Checking final data status..."
sptrader db query "SELECT DATE_TRUNC('month', timestamp) as month, count(*) as ticks FROM market_data_v2 WHERE symbol = 'EURUSD' GROUP BY month ORDER BY month"