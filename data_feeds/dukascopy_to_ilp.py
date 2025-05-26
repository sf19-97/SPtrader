#!/usr/bin/env python3
"""
Bridge between Dukascopy downloader and Go ILP ingestion
*Created: May 25, 2025*
"""

import sys
import json
import subprocess
from datetime import datetime, timezone
from dukascopy_importer import DukascopyDownloader

def main():
    if len(sys.argv) < 4:
        print("Usage: dukascopy_to_ilp.py <symbol> <start_date> <end_date>")
        print("Example: dukascopy_to_ilp.py EURUSD 2024-01-19 2024-01-26")
        sys.exit(1)
    
    symbol = sys.argv[1]
    start_date = datetime.fromisoformat(sys.argv[2]).replace(tzinfo=timezone.utc)
    end_date = datetime.fromisoformat(sys.argv[3]).replace(tzinfo=timezone.utc)
    
    print(f"📊 Downloading {symbol} from {start_date.date()} to {end_date.date()}...")
    
    # Initialize downloader
    downloader = DukascopyDownloader()
    
    # Download data
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
    
    print(f"✅ Downloaded {len(all_records)} ticks")
    
    if all_records:
        print("📤 Sending to ILP ingestion service...")
        
        # Convert to JSON and pipe to Go ingestion service
        json_data = json.dumps(all_records, default=str)
        
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
        print(output)
        
        if process.returncode == 0:
            print("✅ Data successfully ingested via ILP!")
        else:
            print(f"❌ Ingestion failed with code {process.returncode}")
            sys.exit(1)
    else:
        print("❌ No data downloaded")
        sys.exit(1)

if __name__ == "__main__":
    from datetime import timedelta
    main()