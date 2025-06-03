#!/usr/bin/env python3
"""
Dukascopy Historical Data Downloader and QuestDB Importer
Downloads high-quality tick data from Dukascopy and imports into QuestDB
"""

import os
import struct
import lzma
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DukascopyDownloader:
    """Download and process Dukascopy tick data"""
    
    BASE_URL = "https://datafeed.dukascopy.com/datafeed"
    
    # Dukascopy instrument IDs
    INSTRUMENTS = {
        'EURUSD': 'EURUSD',
        'GBPUSD': 'GBPUSD',
        'USDJPY': 'USDJPY',
        'USDCHF': 'USDCHF',
        'AUDUSD': 'AUDUSD',
        'USDCAD': 'USDCAD',
        'NZDUSD': 'NZDUSD',
        'EURGBP': 'EURGBP',
        'EURJPY': 'EURJPY',
        'GBPJPY': 'GBPJPY'
    }
    
    def __init__(self, questdb_url="http://localhost:9000", cache_dir="./dukascopy_cache"):
        self.questdb_url = questdb_url
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create a session for connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def get_tick_url(self, instrument: str, date: datetime, hour: int) -> str:
        """Generate Dukascopy tick data URL"""
        year = date.year
        month = date.month - 1  # Dukascopy uses 0-based months
        day = date.day
        
        return f"{self.BASE_URL}/{instrument}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    
    def download_hour_data(self, instrument: str, date: datetime, hour: int) -> Optional[bytes]:
        """Download one hour of tick data"""
        url = self.get_tick_url(instrument, date, hour)
        
        # Check cache first
        cache_file = os.path.join(
            self.cache_dir, 
            f"{instrument}_{date.strftime('%Y%m%d')}_{hour:02d}.bi5"
        )
        
        if os.path.exists(cache_file):
            logger.debug(f"Using cached file: {cache_file}")
            with open(cache_file, 'rb') as f:
                return f.read()
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200 and len(response.content) > 0:
                # Cache the data
                with open(cache_file, 'wb') as f:
                    f.write(response.content)
                return response.content
            else:
                logger.debug(f"No data for {instrument} {date.date()} {hour:02d}:00")
                return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def decompress_tick_data(self, compressed_data: bytes) -> List[Tuple]:
        """Decompress and parse Dukascopy tick data"""
        try:
            # Decompress LZMA data
            decompressed = lzma.decompress(compressed_data)
            
            # Parse binary format
            # Each tick is 20 bytes: time(4) + ask(4) + bid(4) + ask_vol(4) + bid_vol(4)
            ticks = []
            tick_size = 20
            
            for i in range(0, len(decompressed), tick_size):
                if i + tick_size <= len(decompressed):
                    tick_data = struct.unpack('>IIIff', decompressed[i:i+tick_size])
                    
                    # tick_data = (time_delta, ask, bid, ask_volume, bid_volume)
                    time_delta = tick_data[0]  # milliseconds since hour start
                    ask = tick_data[1] / 100000.0  # Convert to price
                    bid = tick_data[2] / 100000.0
                    ask_volume = tick_data[3]
                    bid_volume = tick_data[4]
                    
                    ticks.append((time_delta, bid, ask, bid_volume, ask_volume))
            
            return ticks
        except Exception as e:
            logger.error(f"Error decompressing data: {e}")
            return []
    
    def process_hour_ticks(self, instrument: str, date: datetime, hour: int, 
                          compressed_data: bytes) -> List[dict]:
        """Process one hour of tick data into records"""
        ticks = self.decompress_tick_data(compressed_data)
        
        if not ticks:
            return []
        
        # Base timestamp for this hour
        base_time = datetime(date.year, date.month, date.day, hour, tzinfo=timezone.utc)
        
        records = []
        for tick in ticks:
            time_delta, bid, ask, bid_vol, ask_vol = tick
            
            # Calculate actual timestamp
            timestamp = base_time + timedelta(milliseconds=time_delta)
            
            # Skip invalid prices
            if bid <= 0 or ask <= 0 or bid >= ask:
                continue
            
            # Calculate derived fields
            mid_price = (bid + ask) / 2
            spread = ask - bid
            total_volume = bid_vol + ask_vol
            
            # Determine trading session
            hour_utc = timestamp.hour
            day_of_week = timestamp.isoweekday()
            session = self.determine_trading_session(hour_utc)
            market_open = self.is_market_open(hour_utc, day_of_week)
            
            record = {
                'timestamp': timestamp.isoformat(),
                'symbol': instrument,
                'bid': bid,
                'ask': ask,
                'price': mid_price,
                'spread': spread,
                'volume': total_volume,
                'bid_volume': bid_vol,
                'ask_volume': ask_vol,
                'hour_of_day': hour_utc,
                'day_of_week': day_of_week,
                'trading_session': session,
                'market_open': market_open
            }
            
            records.append(record)
        
        return records
    
    def determine_trading_session(self, hour: int) -> str:
        """Determine trading session based on UTC hour"""
        if 0 <= hour < 6:
            return "SYDNEY_TOKYO"
        elif hour == 8:
            return "TOKYO_LONDON"
        elif 13 <= hour < 17:
            return "LONDON_NEW_YORK"
        elif 21 <= hour or hour < 6:
            return "SYDNEY"
        elif 0 <= hour < 9:
            return "TOKYO"
        elif 8 <= hour < 17:
            return "LONDON"
        elif 13 <= hour < 22:
            return "NEW_YORK"
        else:
            return "CLOSED"
    
    def is_market_open(self, hour: int, day_of_week: int) -> bool:
        """Check if forex market is open"""
        if day_of_week == 5:  # Friday
            return hour < 22
        elif day_of_week == 6:  # Saturday
            return False
        elif day_of_week == 7:  # Sunday
            return hour >= 22
        else:  # Monday-Thursday
            return True
    
    def create_tables(self):
        """Create or update QuestDB tables for Dukascopy data"""
        # Create enhanced market_data table with volume info
        create_market_data = """
        CREATE TABLE IF NOT EXISTS market_data_v2 (
            timestamp TIMESTAMP,
            symbol SYMBOL,
            bid DOUBLE,
            ask DOUBLE,
            price DOUBLE,
            spread DOUBLE,
            volume DOUBLE,
            bid_volume DOUBLE,
            ask_volume DOUBLE,
            hour_of_day INT,
            day_of_week INT,
            trading_session SYMBOL,
            market_open BOOLEAN
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        
        # Create OHLCV tables with real volume
        timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
        for tf in timeframes:
            create_ohlc = f"""
            CREATE TABLE IF NOT EXISTS ohlc_{tf}_v2 (
                timestamp TIMESTAMP,
                symbol SYMBOL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                tick_count LONG,
                vwap DOUBLE,
                trading_session SYMBOL
            ) timestamp(timestamp) PARTITION BY DAY;
            """
            
            self.execute_query(create_ohlc)
            logger.info(f"Created/verified ohlc_{tf}_v2 table")
        
        self.execute_query(create_market_data)
        logger.info("Created/verified market_data_v2 table")
    
    def execute_query(self, query: str) -> Optional[dict]:
        """Execute SQL query on QuestDB"""
        try:
            response = self.session.get(
                f"{self.questdb_url}/exec",
                params={"query": query},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Query failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def insert_batch(self, records: List[dict]) -> bool:
        """Insert batch of records into QuestDB"""
        if not records:
            return True
        
        # Build bulk insert query
        values = []
        for r in records:
            values.append(
                f"('{r['timestamp']}', '{r['symbol']}', "
                f"{r['bid']}, {r['ask']}, {r['price']}, {r['spread']}, "
                f"{r['volume']}, {r['bid_volume']}, {r['ask_volume']}, "
                f"{r['hour_of_day']}, {r['day_of_week']}, '{r['trading_session']}', "
                f"{r['market_open']})"
            )
        
        # Insert in chunks of 1000 to avoid query size limits
        chunk_size = 1000
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i + chunk_size]
            query = f"""
            INSERT INTO market_data_v2 VALUES {', '.join(chunk)};
            """
            
            result = self.execute_query(query)
            if result is None:
                return False
        
        return True
    
    def download_date_range(self, instrument: str, start_date: datetime, 
                           end_date: datetime, max_workers: int = 10):
        """Download data for a date range using parallel processing"""
        logger.info(f"Downloading {instrument} from {start_date.date()} to {end_date.date()}")
        
        # Generate list of all hours to download
        tasks = []
        current = start_date
        while current <= end_date:
            # Skip weekends (market closed)
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                for hour in range(24):
                    tasks.append((instrument, current, hour))
            current += timedelta(days=1)
        
        logger.info(f"Total hours to process: {len(tasks)}")
        
        # Process in parallel
        processed_count = 0
        error_count = 0
        total_ticks = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                future = executor.submit(self.process_single_hour, *task)
                future_to_task[future] = task
            
            # Process completed tasks
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    tick_count = future.result()
                    if tick_count > 0:
                        processed_count += 1
                        total_ticks += tick_count
                        
                        if processed_count % 100 == 0:
                            logger.info(f"Progress: {processed_count}/{len(tasks)} hours, "
                                      f"{total_ticks:,} ticks")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing {task}: {e}")
        
        logger.info(f"Completed {instrument}: {processed_count} hours, "
                   f"{total_ticks:,} total ticks, {error_count} errors")
        
        return total_ticks
    
    def process_single_hour(self, instrument: str, date: datetime, hour: int) -> int:
        """Process a single hour of data"""
        # Download data
        compressed_data = self.download_hour_data(instrument, date, hour)
        if not compressed_data:
            return 0
        
        # Process ticks
        records = self.process_hour_ticks(instrument, date, hour, compressed_data)
        if not records:
            return 0
        
        # Insert into database
        success = self.insert_batch(records)
        if success:
            return len(records)
        else:
            raise Exception("Failed to insert batch")
    
    def generate_ohlcv(self, timeframe: str = '1m'):
        """Generate OHLCV data from tick data"""
        logger.info(f"Generating {timeframe} OHLCV data...")
        
        query = f"""
        INSERT INTO ohlc_{timeframe}_v2
        SELECT 
            timestamp,
            symbol,
            first(price) AS open,
            max(price) AS high,
            min(price) AS low,
            last(price) AS close,
            sum(volume) AS volume,
            count(*) AS tick_count,
            sum(price * volume) / sum(volume) AS vwap,
            first(trading_session) AS trading_session
        FROM market_data_v2
        WHERE volume > 0
        SAMPLE BY {timeframe} ALIGN TO CALENDAR
        """
        
        result = self.execute_query(query)
        if result:
            logger.info(f"Successfully generated {timeframe} OHLCV data")
        else:
            logger.error(f"Failed to generate {timeframe} OHLCV data")
    
    def get_data_summary(self):
        """Get summary of downloaded data"""
        query = """
        SELECT 
            symbol,
            count(*) as tick_count,
            min(timestamp) as first_tick,
            max(timestamp) as last_tick,
            avg(spread) as avg_spread,
            sum(volume) as total_volume
        FROM market_data_v2
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result = self.execute_query(query)
        if result and result.get('dataset'):
            print("\n📊 Data Summary:")
            print(f"{'Symbol':<10} {'Ticks':<15} {'First':<20} {'Last':<20} {'Avg Spread':<12} {'Total Volume':<15}")
            print("-" * 100)
            
            for row in result['dataset']:
                symbol, ticks, first, last, spread, volume = row
                print(f"{symbol:<10} {ticks:<15,} {first:<20} {last:<20} {spread:<12.5f} {volume:<15,.2f}")


def main():
    """Main function to download Dukascopy data"""
    print("=== Dukascopy Data Downloader ===")
    
    downloader = DukascopyDownloader()
    
    # Create tables
    print("\n📁 Setting up database tables...")
    downloader.create_tables()
    
    # Test connection
    result = downloader.execute_query("SELECT 1")
    if not result:
        print("❌ Cannot connect to QuestDB")
        return
    
    print("✅ Connected to QuestDB")
    
    # Interactive menu
    while True:
        print("\n🔧 Options:")
        print("1. Download last 7 days (all pairs)")
        print("2. Download last 30 days (all pairs)")
        print("3. Download custom range")
        print("4. Download specific pair")
        print("5. Generate OHLCV data")
        print("6. Show data summary")
        print("0. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            # Last 7 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            for instrument in downloader.INSTRUMENTS:
                downloader.download_date_range(instrument, start_date, end_date)
            
            # Generate OHLCV
            for tf in ['1m', '5m', '15m', '1h']:
                downloader.generate_ohlcv(tf)
        
        elif choice == '2':
            # Last 30 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            for instrument in downloader.INSTRUMENTS:
                downloader.download_date_range(instrument, start_date, end_date)
            
            # Generate OHLCV
            for tf in ['1m', '5m', '15m', '1h']:
                downloader.generate_ohlcv(tf)
        
        elif choice == '3':
            # Custom range
            days_back = int(input("Days back from today: "))
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            print("\nSelect instruments (comma-separated or 'all'):")
            print(f"Available: {', '.join(downloader.INSTRUMENTS.keys())}")
            selection = input("Selection: ").strip()
            
            if selection.lower() == 'all':
                instruments = list(downloader.INSTRUMENTS.keys())
            else:
                instruments = [s.strip().upper() for s in selection.split(',')]
            
            for instrument in instruments:
                if instrument in downloader.INSTRUMENTS:
                    downloader.download_date_range(instrument, start_date, end_date)
                else:
                    print(f"⚠️  Unknown instrument: {instrument}")
        
        elif choice == '4':
            # Specific pair
            print(f"\nAvailable: {', '.join(downloader.INSTRUMENTS.keys())}")
            instrument = input("Instrument: ").strip().upper()
            
            if instrument not in downloader.INSTRUMENTS:
                print("❌ Invalid instrument")
                continue
            
            days_back = int(input("Days back from today: "))
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            downloader.download_date_range(instrument, start_date, end_date)
        
        elif choice == '5':
            # Generate OHLCV
            print("\nGenerating all OHLCV timeframes...")
            for tf in ['1m', '5m', '15m', '30m', '1h', '4h', '1d']:
                downloader.generate_ohlcv(tf)
        
        elif choice == '6':
            # Show summary
            downloader.get_data_summary()
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
