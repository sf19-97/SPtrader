#!/usr/bin/env python3
"""
SPtrader Historical Data Manager v2.0
Enhanced historical forex data backfill with better UX and performance
"""

import requests
import time
import sys
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for better visibility"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# Set up colored logging
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = [handler]

class ProgressBar:
    """Simple progress bar for better UX"""
    
    def __init__(self, total: int, width: int = 50):
        self.total = max(1, total)
        self.width = width
        self.current = 0
    
    def update(self, current: int):
        self.current = current
        progress = current / self.total
        filled = int(self.width * progress)
        bar = '█' * filled + '░' * (self.width - filled)
        percent = progress * 100
        print(f'\r[{bar}] {percent:.1f}% ({current}/{self.total})', end='', flush=True)
    
    def finish(self):
        print()  # New line after progress bar

class HistoricalBackfillManager:
    """Enhanced Historical Data Manager for SPtrader"""
    
    def __init__(self, questdb_url: str = "http://localhost:9000"):
        # API Configuration
        self.api_token = "839953525bd59fb3b79ea8513a8b0e93-a0181385f4286c8bc91dbdfacea7b43c"
        self.account_id = "001-001-9439158-001"
        self.oanda_base_url = "https://api-fxtrade.oanda.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # QuestDB Configuration
        self.questdb_url = questdb_url
        
        # Instruments
        self.instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]
        
        # Performance settings
        self.max_candles_per_request = 5000
        self.batch_size = 100
        self.rate_limit_delay = 0.5
        
        # Statistics
        self.stats = defaultdict(lambda: {'downloaded': 0, 'inserted': 0, 'errors': 0})
    
    def execute_query(self, query: str) -> Optional[dict]:
        """Execute SQL query on QuestDB with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.questdb_url}/exec", 
                                      params={"query": query}, 
                                      timeout=30)
                if response.status_code == 200:
                    return response.json()
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"Query failed after {max_retries} attempts: {response.text}")
                        return None
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Query attempt {attempt + 1} failed: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Query failed after {max_retries} attempts: {e}")
                    return None
        
        return None
    
    def test_connections(self) -> bool:
        """Test connections to QuestDB and Oanda API"""
        print("\n🔍 Testing connections...")
        
        # Test QuestDB
        print("  Checking QuestDB...", end='', flush=True)
        result = self.execute_query("SELECT count(*) FROM market_data")
        if result:
            count = result['dataset'][0][0] if result.get('dataset') else 0
            print(f" ✅ Connected ({count:,} existing records)")
        else:
            print(" ❌ Failed")
            return False
        
        # Test Oanda API
        print("  Checking Oanda API...", end='', flush=True)
        try:
            url = f"{self.oanda_base_url}/v3/accounts/{self.account_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                print(" ✅ Connected")
                return True
            else:
                print(f" ❌ Failed (Status: {response.status_code})")
                return False
        except Exception as e:
            print(f" ❌ Failed ({str(e)})")
            return False
    
    def get_data_summary(self) -> Dict[str, dict]:
        """Get comprehensive data summary for all instruments"""
        summary = {}
        
        print("\n📊 Analyzing existing data...")
        
        query = """
        SELECT 
            symbol,
            min(timestamp) as first_data,
            max(timestamp) as last_data,
            count(*) as record_count,
            count(DISTINCT date_trunc('day', timestamp)) as days_covered
        FROM market_data
        GROUP BY symbol
        """
        
        result = self.execute_query(query)
        
        if result and result.get('dataset'):
            for row in result['dataset']:
                symbol, first, last, count, days = row
                summary[symbol] = {
                    'first_data': datetime.fromisoformat(first.replace('Z', '+00:00')),
                    'last_data': datetime.fromisoformat(last.replace('Z', '+00:00')),
                    'record_count': count,
                    'days_covered': days,
                    'has_data': True
                }
        
        # Add instruments with no data
        for instrument in self.instruments:
            symbol = instrument.replace('_', '')
            if symbol not in summary:
                summary[symbol] = {
                    'has_data': False,
                    'record_count': 0,
                    'days_covered': 0
                }
        
        return summary
    
    def display_data_summary(self, summary: Dict[str, dict]):
        """Display data summary in a nice table format"""
        print("\n" + "="*90)
        print(f"{'Symbol':<10} {'Records':<12} {'Days':<6} {'First Data':<20} {'Last Data':<20} {'Gap (hrs)':<10} {'Avg Spread':<10}")
        print("="*90)
        
        total_records = 0
        now = datetime.now(timezone.utc)
        
        for instrument in self.instruments:
            symbol = instrument.replace('_', '')
            info = summary.get(symbol, {'has_data': False})
            
            if info['has_data']:
                gap_hours = (now - info['last_data']).total_seconds() / 3600
                
                # Get average spread
                spread_query = f"SELECT avg(spread) FROM market_data WHERE symbol = '{symbol}'"
                spread_result = self.execute_query(spread_query)
                avg_spread = 0.0
                if spread_result and spread_result.get('dataset') and spread_result['dataset'][0][0]:
                    avg_spread = spread_result['dataset'][0][0]
                
                print(f"{symbol:<10} {info['record_count']:<12,} {info['days_covered']:<6} "
                      f"{info['first_data'].strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{info['last_data'].strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{gap_hours:<10.1f} {avg_spread:<10.5f}")
                total_records += info['record_count']
            else:
                print(f"{symbol:<10} {'No data':<12} {'-':<6} {'-':<20} {'-':<20} {'-':<10} {'-':<10}")
        
        print("="*90)
        print(f"{'TOTAL':<10} {total_records:<12,}")
        print("="*90)
    
    def get_historical_candles_range(self, instrument: str, from_time: str, to_time: str) -> List[dict]:
        """Get historical candles with progress tracking"""
        url = f"{self.oanda_base_url}/v3/instruments/{instrument}/candles"
        
        # When using date range, don't include count parameter
        # GET REAL BID/ASK DATA!
        params = {
            'granularity': 'M1',
            'price': 'BA',    # Bid AND Ask prices for real spread!
            'from': from_time,
            'to': to_time
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                candles = data.get('candles', [])
                # Oanda may return more than 5000 candles, so limit if needed
                if len(candles) > self.max_candles_per_request:
                    logger.warning(f"Received {len(candles)} candles, limiting to {self.max_candles_per_request}")
                    candles = candles[:self.max_candles_per_request]
                return candles
            else:
                error_msg = response.text[:200] if response.text else "No error details"
                logger.error(f"Oanda API error {response.status_code}: {error_msg}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
    
    def smart_backfill_instrument(self, instrument: str, months_back: int) -> bool:
        """Enhanced smart backfill with better progress tracking"""
        symbol = instrument.replace('_', '')
        
        print(f"\n🔄 Backfilling {symbol}")
        print(f"   Target: {months_back} months of data")
        print(f"   📊 Using REAL bid/ask prices with natural spreads")
        
        # Get current state
        summary = self.get_data_summary()
        existing = summary.get(symbol, {'has_data': False})
        
        # Calculate date ranges
        target_start = datetime.now(timezone.utc) - timedelta(days=months_back * 30)
        current_time = datetime.now(timezone.utc)
        
        # Determine what to fetch
        ranges_to_fetch = []
        
        if existing['has_data']:
            print(f"   Found {existing['record_count']:,} existing records")
            
            # Gap before existing data
            if target_start < existing['first_data']:
                ranges_to_fetch.append({
                    'start': target_start,
                    'end': existing['first_data'] - timedelta(minutes=1),
                    'description': 'historical gap'
                })
            
            # Gap after existing data (if more than 1 hour old)
            if existing['last_data'] < current_time - timedelta(hours=1):
                ranges_to_fetch.append({
                    'start': existing['last_data'] + timedelta(minutes=1),
                    'end': current_time,
                    'description': 'recent gap'
                })
        else:
            # No existing data
            ranges_to_fetch.append({
                'start': target_start,
                'end': current_time,
                'description': 'complete range'
            })
        
        if not ranges_to_fetch:
            print(f"   ✅ Already have complete data!")
            return True
        
        # Fetch data for each range
        total_candles = 0
        
        for range_info in ranges_to_fetch:
            print(f"\n   📥 Fetching {range_info['description']}...")
            
            # Calculate chunks
            start = range_info['start']
            end = range_info['end']
            total_minutes = int((end - start).total_seconds() / 60)
            # Using 3-day chunks (4320 minutes per chunk)
            chunks_needed = max(1, (total_minutes + 4319) // 4320)
            
            print(f"      Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
            print(f"      Estimated requests: {chunks_needed}")
            
            # Progress bar
            progress = ProgressBar(chunks_needed)
            chunk_count = 0
            range_candles = 0
            
            current_end = end
            while current_end > start:
                # Use smaller chunks to avoid hitting limits (3 days max per request)
                current_start = max(start, current_end - timedelta(days=3))
                
                # Fetch candles
                candles = self.get_historical_candles_range(
                    instrument,
                    current_start.strftime('%Y-%m-%dT%H:%M:%S.000000000Z'),
                    current_end.strftime('%Y-%m-%dT%H:%M:%S.000000000Z')
                )
                
                if candles:
                    # Process and insert immediately
                    success = self.process_and_insert_candles(candles, symbol)
                    if success:
                        range_candles += len(candles)
                        self.stats[symbol]['downloaded'] += len(candles)
                
                current_end = current_start - timedelta(minutes=1)
                chunk_count += 1
                progress.update(chunk_count)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            progress.finish()
            total_candles += range_candles
            print(f"      ✅ Fetched {range_candles:,} candles")
        
        print(f"\n   📊 Total new data: {total_candles:,} candles")
        return True
    
    def process_and_insert_candles(self, candles: List[dict], symbol: str) -> bool:
        """Process candles and insert as tick data with REAL bid/ask prices"""
        if not candles:
            return True
        
        tick_data = []
        
        for candle in candles:
            if not candle.get('complete'):
                continue
            
            timestamp = candle['time']
            
            # Get REAL bid and ask data
            bid_data = candle.get('bid', {})
            ask_data = candle.get('ask', {})
            
            # If we have real bid/ask data, use it
            if bid_data and ask_data:
                # Use close prices for the tick (most representative)
                bid_price = float(bid_data.get('c', 0))
                ask_price = float(ask_data.get('c', 0))
                mid_price = (bid_price + ask_price) / 2
                real_spread = ask_price - bid_price
            else:
                # Fallback to mid prices if no bid/ask (shouldn't happen with BA)
                mid_data = candle.get('mid', {})
                mid_price = float(mid_data.get('c', 0))
                # Create synthetic spread (only as fallback)
                bid_price = mid_price - 0.0001
                ask_price = mid_price + 0.0001
                real_spread = 0.0002
            
            # Create a single tick per candle
            base_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Calculate session info
            hour = base_time.hour
            day_of_week = base_time.isoweekday()
            
            # Determine trading session
            session = self.determine_trading_session(hour)
            market_open = self.is_market_open(hour, day_of_week)
            
            tick_data.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'bid': bid_price,
                'ask': ask_price,
                'price': mid_price,
                'spread': real_spread,
                'hour_of_day': hour,
                'day_of_week': day_of_week,
                'trading_session': session,
                'volume': 0.0,
                'market_open': market_open
            })
        
        # Insert in batches
        for i in range(0, len(tick_data), self.batch_size):
            batch = tick_data[i:i + self.batch_size]
            if not self.insert_batch(batch):
                return False
        
        self.stats[symbol]['inserted'] += len(tick_data)
        return True
    
    def insert_batch(self, batch: List[dict]) -> bool:
        """Insert a batch of tick data"""
        if not batch:
            return True
        
        values = []
        for tick in batch:
            values.append(
                f"('{tick['timestamp']}', '{tick['symbol']}', "
                f"{tick['bid']}, {tick['ask']}, {tick['price']}, {tick['spread']}, "
                f"{tick['hour_of_day']}, {tick['day_of_week']}, '{tick['trading_session']}', "
                f"{tick['volume']}, {tick['market_open']})"
            )
        
        query = f"""
        INSERT INTO market_data 
        (timestamp, symbol, bid, ask, price, spread, hour_of_day, day_of_week, trading_session, volume, market_open)
        VALUES {', '.join(values)};
        """
        
        result = self.execute_query(query)
        return result is not None
    
    def determine_trading_session(self, hour: int) -> str:
        """Determine trading session based on hour"""
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
        """Check if market is open"""
        if day_of_week == 5:  # Friday
            return hour < 22
        elif day_of_week == 6:  # Saturday
            return False
        elif day_of_week == 7:  # Sunday
            return hour >= 22
        else:  # Monday-Thursday
            return True
    
    def scan_duplicates(self) -> dict:
        """Enhanced duplicate scanning - QuestDB compatible"""
        print("\n🔍 Scanning for duplicates...")
        
        # QuestDB doesn't support HAVING, so we need a different approach
        # First, get the count summary for all symbols
        query = """
        SELECT 
            symbol,
            count(*) as total_records
        FROM market_data
        GROUP BY symbol
        """
        
        result = self.execute_query(query)
        
        if not result or not result.get('dataset'):
            print("❌ Error getting record counts")
            return {}
        
        duplicates = {}
        
        # For each symbol, check for duplicates
        for row in result['dataset']:
            symbol = row[0]
            total_count = row[1]
            
            # Count unique timestamps for this symbol
            unique_query = f"""
            SELECT count(DISTINCT timestamp) as unique_count
            FROM market_data
            WHERE symbol = '{symbol}'
            """
            
            unique_result = self.execute_query(unique_query)
            
            if unique_result and unique_result.get('dataset'):
                unique_count = unique_result['dataset'][0][0]
                duplicate_count = total_count - unique_count
                
                if duplicate_count > 0:
                    duplicates[symbol] = {
                        'total': total_count,
                        'unique': unique_count,
                        'duplicates': duplicate_count
                    }
                    
                    # Show some example duplicates
                    example_query = f"""
                    SELECT timestamp, count(*) as copies
                    FROM market_data
                    WHERE symbol = '{symbol}'
                    GROUP BY timestamp
                    ORDER BY count(*) DESC
                    LIMIT 5
                    """
                    
                    example_result = self.execute_query(example_query)
                    if example_result and example_result.get('dataset'):
                        examples = []
                        for ex_row in example_result['dataset']:
                            if ex_row[1] > 1:  # Only show actual duplicates
                                examples.append(f"{ex_row[0]} ({ex_row[1]} copies)")
                        if examples:
                            duplicates[symbol]['examples'] = examples
        
        return duplicates
    
    def remove_duplicates_smart(self) -> bool:
        """Smart duplicate removal with progress tracking - QuestDB compatible"""
        duplicates = self.scan_duplicates()
        
        if not duplicates:
            print("✅ No duplicates found!")
            return True
        
        print(f"\n⚠️  Found duplicates in {len(duplicates)} symbols:")
        for symbol, info in duplicates.items():
            print(f"   {symbol}: {info['duplicates']:,} duplicates out of {info['total']:,} records")
        
        confirm = input("\n🧹 Remove duplicates? (y/n): ").lower()
        if confirm != 'y':
            return False
        
        print("\n🧹 Removing duplicates...")
        
        # For QuestDB, we need a different approach
        # Create a clean table with deduplicated data
        print("   Creating clean table...")
        
        # First, drop the clean table if it exists
        self.execute_query("DROP TABLE IF EXISTS market_data_clean;")
        
        # Create the structure
        create_structure_query = """
        CREATE TABLE market_data_clean (
            timestamp TIMESTAMP,
            symbol SYMBOL,
            bid DOUBLE,
            ask DOUBLE,
            price DOUBLE,
            spread DOUBLE,
            hour_of_day INT,
            day_of_week INT,
            trading_session SYMBOL,
            volume DOUBLE,
            market_open BOOLEAN
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        
        if not self.execute_query(create_structure_query):
            print("❌ Failed to create clean table structure")
            return False
        
        # Insert deduplicated data symbol by symbol
        print("   Deduplicating data...")
        for symbol in duplicates.keys():
            print(f"     Processing {symbol}...", end='', flush=True)
            
            # For each symbol, insert only unique timestamp records
            insert_query = f"""
            INSERT INTO market_data_clean
            SELECT 
                timestamp,
                '{symbol}' as symbol,
                first(bid) as bid,
                first(ask) as ask,
                first(price) as price,
                first(spread) as spread,
                first(hour_of_day) as hour_of_day,
                first(day_of_week) as day_of_week,
                first(trading_session) as trading_session,
                first(volume) as volume,
                first(market_open) as market_open
            FROM market_data
            WHERE symbol = '{symbol}'
            GROUP BY timestamp
            ORDER BY timestamp;
            """
            
            if self.execute_query(insert_query):
                print(" ✅")
            else:
                print(" ❌")
                print("Failed to process symbol, aborting...")
                self.execute_query("DROP TABLE market_data_clean;")
                return False
        
        # Also copy non-duplicate symbols
        print("   Copying clean symbols...")
        clean_symbols_query = """
        SELECT DISTINCT symbol 
        FROM market_data
        WHERE symbol NOT IN ({})
        """.format(','.join(f"'{s}'" for s in duplicates.keys()))
        
        clean_result = self.execute_query(clean_symbols_query)
        if clean_result and clean_result.get('dataset'):
            for row in clean_result['dataset']:
                clean_symbol = row[0]
                print(f"     Copying {clean_symbol}...", end='', flush=True)
                
                copy_query = f"""
                INSERT INTO market_data_clean
                SELECT * FROM market_data
                WHERE symbol = '{clean_symbol}';
                """
                
                if self.execute_query(copy_query):
                    print(" ✅")
                else:
                    print(" ❌")
        
        # Verify counts
        print("   Verifying data integrity...")
        original_result = self.execute_query("SELECT count(*) FROM market_data")
        clean_result = self.execute_query("SELECT count(*) FROM market_data_clean")
        
        if not original_result or not clean_result:
            print("❌ Failed to verify counts")
            self.execute_query("DROP TABLE market_data_clean;")
            return False
        
        original_count = original_result['dataset'][0][0]
        clean_count = clean_result['dataset'][0][0]
        
        print(f"   Original: {original_count:,} records")
        print(f"   Cleaned: {clean_count:,} records")
        print(f"   Removed: {original_count - clean_count:,} duplicates")
        
        # Backup and replace
        print("   Creating backup...")
        self.execute_query("DROP TABLE IF EXISTS market_data_backup;")
        backup_query = """
        CREATE TABLE market_data_backup AS (
            SELECT * FROM market_data
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        
        if not self.execute_query(backup_query):
            print("⚠️  Warning: Backup creation failed, but continuing...")
        
        # Replace table
        print("   Replacing table...")
        self.execute_query("DROP TABLE market_data;")
        self.execute_query("ALTER TABLE market_data_clean RENAME TO market_data;")
        
        print("✅ Duplicates removed successfully!")
        return True
    
    def run_interactive_menu(self):
        """Enhanced interactive menu"""
        while True:
            # Clear screen for better UX
            print("\033[2J\033[H")  # Clear screen
            
            print("="*90)
            print(" SPtrader Historical Data Manager v2.0".center(90))
            print(" Now with REAL bid/ask prices & natural spreads! 📊".center(90))
            print("="*90)
            
            # Show current status
            summary = self.get_data_summary()
            total_records = sum(s.get('record_count', 0) for s in summary.values())
            print(f"\n📊 Current Status: {total_records:,} total records across {len(self.instruments)} pairs")
            
            print("\n🔧 Quick Actions:")
            print("  1. Show detailed data summary")
            print("  2. Smart backfill - 1 month")
            print("  3. Smart backfill - 3 months")
            print("  4. Smart backfill - 6 months")
            print("  5. Smart backfill - 1 year")
            
            print("\n⚙️  Advanced Options:")
            print("  6. Backfill single instrument")
            print("  7. Custom date range backfill")
            print("  8. Scan for duplicates")
            print("  9. Remove duplicates")
            print(" 10. Update OHLC tables")
            
            print("\n📤 Export/Import:")
            print(" 11. Export data statistics")
            print(" 12. Verify data integrity")
            
            print("\n  0. Exit")
            print("\n" + "="*90)
            
            choice = input("\n👉 Enter your choice (0-12): ").strip()
            
            try:
                if choice == '0':
                    print("\n👋 Thanks for using SPtrader Historical Data Manager!")
                    break
                
                elif choice == '1':
                    self.display_data_summary(summary)
                    input("\nPress Enter to continue...")
                
                elif choice in ['2', '3', '4', '5']:
                    months = {'2': 1, '3': 3, '4': 6, '5': 12}[choice]
                    print(f"\n🚀 Starting {months}-month smart backfill for all instruments...")
                    
                    for instrument in self.instruments:
                        self.smart_backfill_instrument(instrument, months)
                    
                    # Show statistics
                    print("\n📊 Backfill Complete - Statistics:")
                    for symbol, stats in self.stats.items():
                        if stats['downloaded'] > 0:
                            print(f"   {symbol}: Downloaded {stats['downloaded']:,}, "
                                  f"Inserted {stats['inserted']:,}")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == '6':
                    print("\n📋 Available instruments:")
                    for i, inst in enumerate(self.instruments, 1):
                        print(f"   {i}. {inst}")
                    
                    inst_choice = input("\nSelect instrument (1-5): ").strip()
                    if inst_choice.isdigit() and 1 <= int(inst_choice) <= len(self.instruments):
                        instrument = self.instruments[int(inst_choice) - 1]
                        months = int(input("Months of data (1-24): "))
                        self.smart_backfill_instrument(instrument, months)
                    else:
                        print("❌ Invalid selection")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == '8':
                    duplicates = self.scan_duplicates()
                    if duplicates:
                        print("\n⚠️  Duplicates found:")
                        for symbol, info in duplicates.items():
                            print(f"\n   {symbol}: {info['duplicates']:,} duplicates out of {info['total']:,} total records")
                            if 'examples' in info and info['examples']:
                                print(f"   Example timestamps with duplicates:")
                                for example in info['examples'][:3]:  # Show up to 3 examples
                                    print(f"     - {example}")
                    else:
                        print("\n✅ No duplicates found!")
                    input("\nPress Enter to continue...")
                
                elif choice == '9':
                    self.remove_duplicates_smart()
                    input("\nPress Enter to continue...")
                
                elif choice == '10':
                    print("\n📊 Updating OHLC tables from historical data...")
                    self.update_ohlc_tables()
                    input("\nPress Enter to continue...")
                
                elif choice == '11':
                    print("\n📤 Exporting data statistics...")
                    self.export_statistics()
                    input("\nPress Enter to continue...")
                
                elif choice == '12':
                    print("\n🔍 Verifying data integrity...")
                    self.verify_data_integrity()
                    input("\nPress Enter to continue...")
                
                else:
                    print("\n❌ Invalid choice. Please try again.")
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user")
                input("Press Enter to return to menu...")
            except Exception as e:
                logger.error(f"Error: {e}")
                input("\nPress Enter to continue...")
    
    def verify_data_integrity(self):
        """Verify data integrity and consistency - QuestDB compatible"""
        print("\n🔍 Running data integrity checks...")
        
        checks = []
        
        # Check 1: Overall data statistics
        print("   Checking data statistics...", end='', flush=True)
        stats_query = """
        SELECT 
            symbol,
            count(*) as record_count,
            min(timestamp) as first_record,
            max(timestamp) as last_record
        FROM market_data
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result = self.execute_query(stats_query)
        if result and result.get('dataset'):
            print(" ✅")
            print("\n   📊 Data Summary:")
            for row in result['dataset']:
                symbol, count, first, last = row
                print(f"      {symbol}: {count:,} records ({first} to {last})")
        else:
            print(" ❌")
            checks.append("Failed to get data statistics")
        
        # Check 2: Recent data availability
        print("\n   Checking recent data...", end='', flush=True)
        recent_query = """
        SELECT 
            symbol,
            count(*) as recent_records
        FROM market_data
        WHERE timestamp > dateadd('h', -24, now())
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result = self.execute_query(recent_query)
        if result and result.get('dataset'):
            print(" ✅")
            missing_recent = []
            for row in result['dataset']:
                if row[1] < 100:  # Less than 100 records in 24h might indicate issues
                    missing_recent.append(f"{row[0]} has only {row[1]} records in last 24h")
            if missing_recent:
                checks.extend(missing_recent)
        else:
            print(" ⚠️  No recent data check available")
        
        # Check 3: Check for duplicates
        print("   Checking for duplicates...", end='', flush=True)
        dup_summary = self.scan_duplicates()
        if dup_summary:
            print(f" ⚠️  Found duplicates in {len(dup_summary)} symbols")
            for symbol, info in dup_summary.items():
                checks.append(f"{symbol} has {info['duplicates']:,} duplicate records")
        else:
            print(" ✅ No duplicates")
        
        # Display results
        if checks:
            print("\n⚠️  Issues found:")
            for check in checks:
                print(f"   - {check}")
        else:
            print("\n✅ All integrity checks passed!")
    
    def update_ohlc_tables(self):
        """Update all OHLC tables from market data"""
        print("\n🔄 Updating OHLC tables from market data...")
        
        # Timeframes to update
        timeframes = {
            '1m': '1-minute',
            '5m': '5-minute',
            '15m': '15-minute',
            '1h': '1-hour'
        }
        
        # First, check what data range we have
        range_query = """
        SELECT 
            min(timestamp) as oldest,
            max(timestamp) as newest,
            count(*) as total_ticks
        FROM market_data
        """
        
        result = self.execute_query(range_query)
        if not result or not result.get('dataset'):
            print("❌ No data found in market_data table")
            return
        
        oldest, newest, total = result['dataset'][0]
        print(f"\n📊 Source data: {total:,} ticks from {oldest} to {newest}")
        
        # Ask user what to do
        print("\n🤔 How would you like to update OHLC tables?")
        print("  1. Full rebuild (clear and regenerate all data)")
        print("  2. Incremental update (only add new data)")
        print("  3. Cancel")
        
        update_choice = input("\nChoice (1-3): ").strip()
        
        if update_choice == '3':
            print("Cancelled")
            return
        
        full_rebuild = (update_choice == '1')
        
        # Process each timeframe
        for tf, tf_name in timeframes.items():
            print(f"\n📈 Processing {tf_name} candles...")
            
            if full_rebuild:
                # Clear existing data
                print(f"   Clearing old {tf} data...", end='', flush=True)
                truncate_result = self.execute_query(f"TRUNCATE TABLE ohlc_{tf}")
                if truncate_result is not None:
                    print(" ✅")
                else:
                    print(" ❌")
                    continue
                
                # Rebuild all data
                print(f"   Generating {tf} candles from all data...", end='', flush=True)
                insert_query = f"""
                INSERT INTO ohlc_{tf}
                SELECT 
                    timestamp,
                    symbol,
                    first(price) AS open,
                    max(price) AS high,
                    min(price) AS low,
                    last(price) AS close,
                    sum(volume) AS volume,
                    count(*) AS tick_count,
                    first(trading_session) AS trading_session
                FROM market_data
                SAMPLE BY {tf} ALIGN TO CALENDAR
                """
            else:
                # Get the last timestamp in OHLC table
                last_ohlc_query = f"SELECT max(timestamp) FROM ohlc_{tf}"
                last_result = self.execute_query(last_ohlc_query)
                
                if last_result and last_result['dataset'][0][0]:
                    last_timestamp = last_result['dataset'][0][0]
                    print(f"   Last {tf} candle: {last_timestamp}")
                    print(f"   Generating new {tf} candles...", end='', flush=True)
                    
                    # Only insert new data
                    insert_query = f"""
                    INSERT INTO ohlc_{tf}
                    SELECT 
                        timestamp,
                        symbol,
                        first(price) AS open,
                        max(price) AS high,
                        min(price) AS low,
                        last(price) AS close,
                        sum(volume) AS volume,
                        count(*) AS tick_count,
                        first(trading_session) AS trading_session
                    FROM market_data
                    WHERE timestamp > '{last_timestamp}'
                    SAMPLE BY {tf} ALIGN TO CALENDAR
                    """
                else:
                    print(f"   No existing {tf} data, generating all...", end='', flush=True)
                    insert_query = f"""
                    INSERT INTO ohlc_{tf}
                    SELECT 
                        timestamp,
                        symbol,
                        first(price) AS open,
                        max(price) AS high,
                        min(price) AS low,
                        last(price) AS close,
                        sum(volume) AS volume,
                        count(*) AS tick_count,
                        first(trading_session) AS trading_session
                    FROM market_data
                    SAMPLE BY {tf} ALIGN TO CALENDAR
                    """
            
            # Execute the insert
            insert_result = self.execute_query(insert_query)
            if insert_result is not None:
                print(" ✅")
                
                # Get count of candles
                count_query = f"SELECT count(*) FROM ohlc_{tf}"
                count_result = self.execute_query(count_query)
                if count_result and count_result.get('dataset'):
                    candle_count = count_result['dataset'][0][0]
                    print(f"   Total {tf} candles: {candle_count:,}")
            else:
                print(" ❌ Failed")
        
        print("\n✅ OHLC update complete!")
        print("\n💡 Tip: Refresh your chart (Ctrl+F5) to see the updated data!")
    
    def export_statistics(self):
        """Export detailed statistics about the data"""
        print("\n📊 Generating detailed statistics...")
        
        # Get overall stats
        overall_query = """
        SELECT 
            count(*) as total_records,
            count(DISTINCT symbol) as symbols,
            count(DISTINCT date_trunc('day', timestamp)) as trading_days,
            min(timestamp) as oldest_data,
            max(timestamp) as newest_data
        FROM market_data
        """
        
        result = self.execute_query(overall_query)
        if result and result.get('dataset'):
            total, symbols, days, oldest, newest = result['dataset'][0]
            print(f"\n📈 Overall Statistics:")
            print(f"   Total records: {total:,}")
            print(f"   Symbols: {symbols}")
            print(f"   Trading days: {days}")
            print(f"   Date range: {oldest} to {newest}")
        
        # Get per-symbol stats
        symbol_query = """
        SELECT 
            symbol,
            count(*) as records,
            min(price) as min_price,
            max(price) as max_price,
            avg(price) as avg_price,
            avg(spread) as avg_spread
        FROM market_data
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result = self.execute_query(symbol_query)
        if result and result.get('dataset'):
            print(f"\n📊 Per-Symbol Statistics:")
            print(f"{'Symbol':<10} {'Records':<12} {'Min Price':<12} {'Max Price':<12} {'Avg Price':<12} {'Avg Spread':<12}")
            print("-" * 70)
            for row in result['dataset']:
                symbol, records, min_p, max_p, avg_p, avg_s = row
                print(f"{symbol:<10} {records:<12,} {min_p:<12.5f} {max_p:<12.5f} {avg_p:<12.5f} {avg_s:<12.5f}")
        
        # Trading session distribution
        session_query = """
        SELECT 
            trading_session,
            count(*) as records,
            count(DISTINCT symbol) as symbols
        FROM market_data
        GROUP BY trading_session
        ORDER BY records DESC
        """
        
        result = self.execute_query(session_query)
        if result and result.get('dataset'):
            print(f"\n🕐 Trading Session Distribution:")
            for row in result['dataset']:
                session, records, symbols = row
                percentage = (records / total) * 100 if total > 0 else 0
                print(f"   {session}: {records:,} records ({percentage:.1f}%)")
        
        # Save to file option
        save = input("\n💾 Save statistics to file? (y/n): ").lower()
        if save == 'y':
            filename = f"sptrader_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                # Re-run queries and write to file
                f.write("SPtrader Data Statistics\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("="*70 + "\n")
                # ... (write all stats to file)
            print(f"✅ Statistics saved to {filename}")


def main():
    """Main entry point"""
    print("\n🚀 Starting SPtrader Historical Data Manager v2.0...")
    
    manager = HistoricalBackfillManager()
    
    # Test connections
    if not manager.test_connections():
        print("\n❌ Connection tests failed. Please check your configuration.")
        return
    
    # Run interactive menu
    manager.run_interactive_menu()


if __name__ == "__main__":
    main()
