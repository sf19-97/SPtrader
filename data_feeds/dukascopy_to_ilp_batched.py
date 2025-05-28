#!/usr/bin/env python3
"""
Batched bridge between Dukascopy downloader and Go ILP ingestion
Processes data in daily batches to avoid memory issues
*Created: May 27, 2025*
"""

import sys
import json
import subprocess
import os
from datetime import datetime, timezone, timedelta
from dukascopy_importer import DukascopyDownloader

# Configuration
BATCH_DAYS = 3  # Process 3 days at a time
STATE_FILE = "/home/millet_frazier/SPtrader/data_feeds/.batch_progress.json"

def load_progress():
    """Load progress from state file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save progress to state file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def send_to_ilp(records, symbol):
    """Send batch of records to ILP ingestion"""
    if not records:
        return True
    
    print(f"  📤 Sending {len(records)} ticks to ILP...")
    
    # Convert to JSON and pipe to Go ingestion service
    json_data = json.dumps(records, default=str)
    
    # Run the Go ingestion service
    process = subprocess.Popen(
        ['/home/millet_frazier/SPtrader/build/ingestion', '-python'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Send data and get output
    output, _ = process.communicate(input=json_data)
    
    if process.returncode == 0:
        print(f"  ✅ Batch successfully ingested!")
        return True
    else:
        print(f"  ❌ Ingestion failed: {output}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: dukascopy_to_ilp_batched.py <symbol> <start_date> <end_date>")
        print("Example: dukascopy_to_ilp_batched.py EURUSD 2023-10-01 2023-12-31")
        print("\nThis script processes data in batches and can be resumed if interrupted.")
        sys.exit(1)
    
    symbol = sys.argv[1]
    start_date = datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
    end_date = datetime.fromisoformat(sys.argv[3]).replace(tzinfo=timezone.utc)
    
    # Load progress
    progress = load_progress()
    job_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
    
    if job_key in progress:
        last_processed = datetime.fromisoformat(progress[job_key]).replace(tzinfo=timezone.utc)
        print(f"📂 Resuming from {last_processed.date()}...")
        current = last_processed + timedelta(days=1)
    else:
        current = start_date
        print(f"📊 Starting batch download of {symbol} from {start_date.date()} to {end_date.date()}...")
    
    # Initialize downloader
    downloader = DukascopyDownloader()
    
    # Process in batches
    total_ticks = 0
    failed_batches = []
    
    while current <= end_date:
        # Calculate batch end (up to BATCH_DAYS or end_date)
        batch_end = min(current + timedelta(days=BATCH_DAYS - 1), end_date)
        
        print(f"\n🔄 Processing batch: {current.date()} to {batch_end.date()}")
        
        try:
            # Download batch
            print(f"  📥 Downloading...")
            downloader.download_date_range([symbol], current, batch_end)
            
            # Process each day in the batch
            batch_records = []
            batch_current = current
            
            while batch_current <= batch_end:
                for hour in range(24):
                    if batch_current.replace(hour=hour) > batch_end:
                        break
                    
                    # Download hour data
                    data = downloader.download_hour_data(symbol, batch_current, hour)
                    if data:
                        # Process into records
                        records = downloader.process_hour_ticks(symbol, batch_current, hour, data)
                        batch_records.extend(records)
                
                # Move to next day
                batch_current = batch_current.replace(hour=0) + timedelta(days=1)
            
            print(f"  ✅ Downloaded {len(batch_records)} ticks")
            
            # Send batch to ILP
            if batch_records:
                if send_to_ilp(batch_records, symbol):
                    total_ticks += len(batch_records)
                    # Update progress
                    progress[job_key] = batch_end.isoformat()
                    save_progress(progress)
                else:
                    failed_batches.append((current.date(), batch_end.date()))
                    print(f"  ⚠️  Failed to ingest batch {current.date()} to {batch_end.date()}")
            
            # Clear memory
            batch_records = None
            
        except Exception as e:
            print(f"  ❌ Error processing batch: {e}")
            failed_batches.append((current.date(), batch_end.date()))
        
        # Move to next batch
        current = batch_end + timedelta(days=1)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Total ticks ingested: {total_ticks:,}")
    
    if failed_batches:
        print(f"\n⚠️  Failed batches ({len(failed_batches)}):")
        for start, end in failed_batches:
            print(f"   - {start} to {end}")
        print("\nYou can re-run the script to retry failed batches.")
    else:
        print("✅ All batches processed successfully!")
        # Clean up progress for this job
        if job_key in progress:
            del progress[job_key]
            save_progress(progress)
    
    # Check database
    print("\n📊 Checking database...")
    check_cmd = f'sptrader db query "SELECT count(*) FROM market_data_v2 WHERE symbol = \'{symbol}\' AND timestamp >= \'{start_date.date()}\'"'
    os.system(check_cmd)

if __name__ == "__main__":
    main()