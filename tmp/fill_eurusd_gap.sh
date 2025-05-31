#!/bin/bash
# Fill the gap in EURUSD data from March 2024 to May 2025
# Created: May 31, 2025

LOGFILE="/home/millet_frazier/SPtrader/logs/runtime/gap_filling.log"
mkdir -p $(dirname "$LOGFILE")

# Log helper function
log() {
  echo "[$(date "+%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOGFILE"
}

cd /home/millet_frazier/SPtrader/data_feeds

log "=== Starting EURUSD Gap Filling (March 2024 - May 2025) ==="

# Process in 2-month chunks to avoid overwhelming the system
# March-April 2024
log "📅 Processing March-April 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-03-06 2024-04-30
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during March-April 2024 processing"
fi

# May-June 2024
log "📅 Processing May-June 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-05-01 2024-06-30
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during May-June 2024 processing"
fi

# July-August 2024
log "📅 Processing July-August 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-07-01 2024-08-31
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during July-August 2024 processing"
fi

# September-October 2024
log "📅 Processing September-October 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-09-01 2024-10-31
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during September-October 2024 processing"
fi

# November-December 2024
log "📅 Processing November-December 2024..."
python3 dukascopy_to_ilp_batched.py EURUSD 2024-11-01 2024-12-31
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during November-December 2024 processing"
fi

# January-February 2025
log "📅 Processing January-February 2025..."
python3 dukascopy_to_ilp_batched.py EURUSD 2025-01-01 2025-02-28
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during January-February 2025 processing"
fi

# March-April 2025
log "📅 Processing March-April 2025..."
python3 dukascopy_to_ilp_batched.py EURUSD 2025-03-01 2025-04-30
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during March-April 2025 processing"
fi

# May 2025 (up to the 26th, since we have data from the 27th already)
log "📅 Processing May 2025..."
python3 dukascopy_to_ilp_batched.py EURUSD 2025-05-01 2025-05-26
if [ $? -ne 0 ]; then
  log "⚠️ Warning: Errors occurred during May 2025 processing"
fi

# Generate OHLC candles after filling all gaps
log "📊 Generating OHLC candles from new data..."
cd /home/millet_frazier/SPtrader/scripts
python3 simple_ohlc_generator.py EURUSD

log "✅ Gap filling complete! Running final analysis..."

# Check for any remaining gaps
cd /home/millet_frazier/SPtrader/tools
python3 check_data_gaps.py EURUSD --ohlc

log "=== EURUSD Gap Filling Complete ==="