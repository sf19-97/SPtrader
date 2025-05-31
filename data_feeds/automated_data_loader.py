#!/usr/bin/env python3
"""
Automated data loader for SPtrader
Loads market data without starting additional services
*Created: May 30, 2025*
"""

import sys
import json
import subprocess
import os
from datetime import datetime, timezone, timedelta
from dukascopy_importer import DukascopyDownloader

# Configuration
BATCH_DAYS = 1  # Process 1 day at a time
STATE_FILE = "/home/millet_frazier/SPtrader/data_feeds/.auto_load_progress.json"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/data_loader.log"

def log(message):
    """Log to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    # Console output
    print(log_entry)
    
    # File output
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

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
    
    log(f"  📤 Sending {len(records)} ticks to ILP...")
    
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
    
    # Check result
    if process.returncode == 0:
        log(f"  ✅ Successfully ingested {len(records)} ticks")
        return True
    else:
        log(f"  ❌ Ingestion failed: {output}")
        return False

def process_batch(symbol, start_date, end_date):
    """Process a single batch of data"""
    log(f"🔄 Processing batch: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize downloader
    downloader = DukascopyDownloader()
    
    # Download data
    log(f"  📥 Downloading...")
    downloader.download_date_range([symbol], start_date, end_date)
    
    # Get the downloaded data by processing each hour
    all_records = []
    current = start_date
    
    while current <= end_date:
        for hour in range(24):
            if current.replace(hour=hour) > end_date:
                break
                
            # Download hour data
            data = downloader.download_hour_data(symbol, current, hour)
            if data:
                # Process into records
                records = downloader.process_hour_ticks(symbol, current, hour, data)
                all_records.extend(records)
        
        # Move to next day
        current = current.replace(hour=0) + timedelta(days=1)
    
    log(f"  ✅ Downloaded {len(all_records)} ticks")
    
    # Send to ILP
    if all_records:
        return send_to_ilp(all_records, symbol)
    else:
        log("  ⚠️ No data to ingest")
        return True

def get_latest_data_date(symbol):
    """Get the latest date for which we have data for the given symbol"""
    try:
        # Check the database for the latest timestamp
        query = f"SELECT%20MAX(timestamp)%20FROM%20market_data_v2%20WHERE%20symbol='{symbol}'"
        url = f"http://localhost:9000/exec?query={query}"
        
        process = subprocess.run(
            ["curl", "-s", url],
            capture_output=True, 
            text=True
        )
        
        output = process.stdout
        
        # Parse JSON response
        try:
            response = json.loads(output)
            if response and response.get("dataset") and len(response["dataset"]) > 0:
                # Extract timestamp
                latest_timestamp = response["dataset"][0][0]
                if latest_timestamp:
                    # Convert to datetime
                    dt = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                    # Return date only
                    return dt.date()
            
            # If we couldn't get a valid timestamp, return None
            return None
        except Exception as e:
            log(f"❌ Error parsing database response: {e}")
            return None
            
    except Exception as e:
        log(f"❌ Error querying database: {e}")
        return None

def main():
    """Main function"""
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    log("=== Automated Data Loader Started ===")
    
    if len(sys.argv) < 2:
        log("Usage: automated_data_loader.py <symbol> [days_to_load]")
        log("Example: automated_data_loader.py EURUSD 7")
        sys.exit(1)
    
    symbol = sys.argv[1]
    days_to_load = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    # Get the last processed date
    progress = load_progress()
    symbol_progress = progress.get(symbol, {})
    
    # Get last date from database
    latest_db_date = get_latest_data_date(symbol)
    
    if latest_db_date:
        # Start from the day after the latest date in DB
        start_date = (datetime.combine(latest_db_date, datetime.min.time()) + timedelta(days=1)).replace(tzinfo=timezone.utc)
        log(f"📊 Starting from day after latest data in DB: {start_date.strftime('%Y-%m-%d')}")
    else:
        # Start from a default date
        start_date = datetime.now(timezone.utc) - timedelta(days=days_to_load)
        log(f"⚠️ No data found in DB. Starting from {days_to_load} days ago: {start_date.strftime('%Y-%m-%d')}")
    
    # End date is yesterday
    end_date = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    
    log(f"📊 Loading {symbol} data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    # Process data in batches
    current_start = start_date
    total_ticks = 0
    success = True
    
    while current_start <= end_date and success:
        # Calculate batch end
        batch_end = (current_start + timedelta(days=BATCH_DAYS - 1)).replace(hour=23, minute=59, second=59)
        if batch_end > end_date:
            batch_end = end_date
        
        # Process batch
        success = process_batch(symbol, current_start, batch_end)
        
        if success:
            # Update progress
            symbol_progress['last_date'] = batch_end.strftime('%Y-%m-%d')
            progress[symbol] = symbol_progress
            save_progress(progress)
            
            # Move to next batch
            current_start = (batch_end + timedelta(seconds=1)).replace(hour=0, minute=0, second=0)
        else:
            log(f"❌ Failed to process batch {current_start.strftime('%Y-%m-%d')} to {batch_end.strftime('%Y-%m-%d')}")
            break
    
    # Generate OHLC candles
    if success:
        log("📊 Generating OHLC candles...")
        process = subprocess.run(
            ["python3", "/home/millet_frazier/SPtrader/scripts/simple_ohlc_generator.py", symbol],
            capture_output=True,
            text=True
        )
        log(f"OHLC generation output: {process.stdout}")
        if process.returncode == 0:
            log("✅ OHLC candles generated successfully")
        else:
            log(f"❌ OHLC generation failed: {process.stderr}")
    
    log("=== Automated Data Loader Completed ===")

if __name__ == "__main__":
    main()