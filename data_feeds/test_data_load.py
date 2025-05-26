#!/usr/bin/env python3
"""
Test data loading with debug output
*Created: May 25, 2025*
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dukascopy_importer import DukascopyDownloader
from datetime import datetime, timezone

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def main():
    print("🧪 Testing Dukascopy data download...")
    
    downloader = DukascopyDownloader()
    
    # Test downloading one hour of data
    test_date = datetime(2024, 1, 19, tzinfo=timezone.utc)  # Friday Jan 19, 2024
    test_hour = 10  # 10:00 UTC
    
    print(f"\n📅 Testing download for: {test_date.strftime('%Y-%m-%d')} {test_hour:02d}:00 UTC")
    
    # Download one hour
    data = downloader.download_hour_data('EURUSD', test_date, test_hour)
    
    if data:
        print(f"✅ Downloaded {len(data)} bytes")
        
        # Try to decompress
        ticks = downloader.decompress_tick_data(data)
        print(f"✅ Decompressed {len(ticks)} ticks")
        
        if ticks:
            # Show first few ticks
            print("\nFirst 5 ticks:")
            for i, tick in enumerate(ticks[:5]):
                time_delta, bid, ask, bid_vol, ask_vol = tick
                print(f"  {i+1}: time_delta={time_delta}ms, bid={bid:.5f}, ask={ask:.5f}")
                
            # Process and insert
            print("\n📊 Processing ticks...")
            records = downloader.process_hour_ticks('EURUSD', test_date, test_hour, data)
            print(f"✅ Processed {len(records)} valid records")
            
            if records:
                print("\n💾 Inserting into database...")
                downloader.insert_batch(records)
                print("✅ Insertion complete")
                
                # Check database
                result = downloader.execute_query("SELECT count(*) FROM market_data_v2")
                if result and result.get('dataset'):
                    count = result['dataset'][0][0]
                    print(f"\n📊 Total records in database: {count}")
    else:
        print("❌ No data downloaded")
        
        # Test URL generation
        url = downloader.get_tick_url('EURUSD', test_date, test_hour)
        print(f"\n🔗 URL generated: {url}")

if __name__ == "__main__":
    main()