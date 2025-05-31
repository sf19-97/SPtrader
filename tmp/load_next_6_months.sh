#!/bin/bash
# Load next 6 months of historical EURUSD data
# Months to load: Sept 2023 - Feb 2024

echo "🚀 Loading next 6 months of EURUSD historical data..."
echo "==================================================="

cd /home/millet_frazier/SPtrader/data_feeds

# September 2023
echo -e "\n📅 Loading September 2023..."
python3 dukascopy_to_ilp_batched.py EURUSD 2023-09-01 2023-09-30

# October 2023
echo -e "\n📅 Loading October 2023..."
python3 dukascopy_to_ilp_batched.py EURUSD 2023-10-01 2023-10-31

# November 2023
echo -e "\n📅 Loading November 2023..."
python3 dukascopy_to_ilp_batched.py EURUSD 2023-11-01 2023-11-30

# December 2023
echo -e "\n📅 Loading December 2023..."
python3 dukascopy_to_ilp_batched.py EURUSD 2023-12-01 2023-12-31

# January 2024
echo -e "\n📅 Loading January 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-01-01 2024-01-31

# February 2024
echo -e "\n📅 Loading February 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-02-01 2024-02-29

echo -e "\n✅ All months loaded! Checking final data range..."
curl -G 'http://localhost:9000/exec' \
  --data-urlencode "query=SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest, COUNT(*) as total_records FROM market_data_v2 WHERE symbol='EURUSD'" \
  | python3 -m json.tool

echo -e "\n🔄 Generating OHLC candles from new data..."
cd /home/millet_frazier/SPtrader/scripts
python3 simple_ohlc_generator.py EURUSD