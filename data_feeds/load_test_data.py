#!/usr/bin/env python3
"""
Load test data for SPtrader - 1 week of EURUSD
*Created: May 25, 2025*
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dukascopy_importer import DukascopyDownloader
from datetime import datetime, timedelta, timezone

def main():
    print("🚀 Loading test data for SPtrader...")
    print("📊 Target: 1 week of EURUSD data")
    
    downloader = DukascopyDownloader()
    
    # Create tables
    print("\n📁 Setting up database tables...")
    downloader.create_tables()
    
    # Test connection
    result = downloader.execute_query("SELECT 1")
    if not result:
        print("❌ Cannot connect to QuestDB")
        return 1
    
    print("✅ Connected to QuestDB")
    
    # Download 1 week of EURUSD from January 2024 (ensure historical data is available)
    end_date = datetime(2024, 1, 26, 23, 59, 59, tzinfo=timezone.utc)  # Friday Jan 26, 2024
    start_date = datetime(2024, 1, 19, 0, 0, 0, tzinfo=timezone.utc)   # Friday Jan 19, 2024
    
    print(f"\n📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("💱 Symbol: EURUSD")
    
    # Download the data
    downloader.download_date_range(['EURUSD'], start_date, end_date)
    
    # Generate OHLCV data
    print("\n📊 Generating OHLCV data...")
    downloader.generate_ohlcv()
    
    # Show summary
    print("\n✅ Data loading complete!")
    downloader.get_data_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())