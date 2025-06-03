#!/usr/bin/env python3
"""
Dukascopy Data Downloader and Importer
All-in-one tool for downloading and importing Dukascopy forex data to QuestDB
Created: May 31, 2025
"""

import os
import sys
import struct
import lzma
import requests
import yaml
import json
import argparse
import logging
import logging.handlers
import subprocess
from datetime import datetime, timedelta, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional, Any, Union
import pandas as pd
from pathlib import Path
import tempfile

# Script location and directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")
STATE_PATH = os.path.join(SCRIPT_DIR, ".download_state.json")
CACHE_DIR = os.path.join(SCRIPT_DIR, "cache")
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

class DukascopyManager:
    """
    Comprehensive manager for Dukascopy data operations
    Combines downloading, processing, and database integration
    """
    
    # Dukascopy base URL
    BASE_URL = "https://datafeed.dukascopy.com/datafeed"
    
    # Standard forex instruments
    DEFAULT_INSTRUMENTS = {
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
    
    # Default timeframes
    DEFAULT_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    def __init__(self):
        """Initialize the Dukascopy manager with configuration"""
        # Load configuration
        self.config = self.load_config()
        
        # Set up logging
        self.setup_logging()
        
        # Initialize state
        self.state = self.load_state()
        
        # Database connection parameters
        self.db_host = self.config.get('database', {}).get('host', 'localhost')
        self.db_port = self.config.get('database', {}).get('port', 9000)
        self.db_user = self.config.get('database', {}).get('user', 'admin')
        self.db_pass = self.config.get('database', {}).get('password', 'quest')
        self.db_url = f"http://{self.db_host}:{self.db_port}"
        
        # ILP settings
        self.use_ilp = self.config.get('ilp', {}).get('enabled', True)
        self.ilp_port = self.config.get('database', {}).get('ilp_port', 9009)
        self.ilp_batch_size = self.config.get('ilp', {}).get('batch_size', 10000)
        self.ilp_buffer_size = self.config.get('ilp', {}).get('buffer_size', 50000)
        
        # Download settings
        self.cache_dir = self.config.get('download', {}).get('cache_dir', CACHE_DIR)
        self.max_workers = self.config.get('download', {}).get('max_workers', 10)
        self.batch_days = self.config.get('download', {}).get('batch_days', 3)
        self.request_timeout = self.config.get('download', {}).get('timeout', 30)
        
        # OHLC settings
        self.timeframes = self.config.get('ohlc', {}).get('timeframes', self.DEFAULT_TIMEFRAMES)
        self.partition_by = self.config.get('ohlc', {}).get('partition_by', 'DAY')
        
        # Symbols to process
        self.symbols = self.config.get('symbols', list(self.DEFAULT_INSTRUMENTS.keys()))
        
        # Create HTTP session for connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    return yaml.safe_load(f)
            else:
                print(f"Warning: Config file {CONFIG_PATH} not found, using defaults")
                return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def setup_logging(self):
        """Set up logging with rotation"""
        log_file = self.config.get('logging', {}).get('file', 
                                                   os.path.join(LOGS_DIR, 'dukascopy.log'))
        log_level_name = self.config.get('logging', {}).get('level', 'INFO')
        log_level = getattr(logging, log_level_name)
        max_size = self.config.get('logging', {}).get('max_size', 10*1024*1024)  # 10MB
        backup_count = self.config.get('logging', {}).get('backup_count', 5)
        
        # Create a logger
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # Clear existing handlers
        logger.handlers = []
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count
        )
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        self.logger = logger
    
    def load_state(self) -> Dict:
        """Load download state from JSON file"""
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading state file: {e}")
                return {}
        return {}
    
    def save_state(self):
        """Save download state to JSON file"""
        with open(STATE_PATH, 'w') as f:
            json.dump(self.state, f, indent=2)
    
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
            self.logger.debug(f"Using cached file: {cache_file}")
            with open(cache_file, 'rb') as f:
                return f.read()
        
        try:
            response = self.session.get(url, timeout=self.request_timeout)
            if response.status_code == 200 and len(response.content) > 0:
                # Cache the data
                with open(cache_file, 'wb') as f:
                    f.write(response.content)
                return response.content
            else:
                self.logger.debug(f"No data for {instrument} {date.date()} {hour:02d}:00")
                return None
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
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
            self.logger.error(f"Error decompressing data: {e}")
            return []
    
    def process_hour_ticks(self, instrument: str, date: datetime, hour: int, 
                          compressed_data: bytes) -> List[Dict]:
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
                'timestamp': timestamp,
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
        if 0 <= hour < 9:
            return "ASIA"
        elif 7 <= hour < 16:
            return "EUROPE"
        elif 12 <= hour < 21:
            return "US"
        elif hour >= 20 or hour < 3:
            return "OVERLAP"
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
    
    def create_database_tables(self) -> bool:
        """Create or update QuestDB tables for Dukascopy data"""
        self.logger.info("Creating database tables...")
        
        try:
            # Create enhanced market_data table with volume info
            create_market_data = f"""
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
            ) timestamp(timestamp) PARTITION BY {self.partition_by};
            """
            
            self.execute_query(create_market_data)
            self.logger.info("Created/verified market_data_v2 table")
            
            # Create OHLCV tables with real volume
            for tf in self.timeframes:
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
                ) timestamp(timestamp) PARTITION BY {self.partition_by};
                """
                
                self.execute_query(create_ohlc)
                self.logger.info(f"Created/verified ohlc_{tf}_v2 table")
            
            return True
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            return False
    
    def execute_query(self, query: str) -> Optional[Dict]:
        """Execute SQL query on QuestDB"""
        try:
            response = self.session.get(
                f"{self.db_url}/exec",
                params={"query": query},
                timeout=self.request_timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Query failed: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return None
    
    def insert_batch_http(self, records: List[Dict]) -> bool:
        """Insert batch of records using HTTP SQL"""
        if not records:
            return True
        
        # Build bulk insert query
        values = []
        for r in records:
            # Format timestamp for SQL
            timestamp_str = r['timestamp'].isoformat()
            
            values.append(
                f"('{timestamp_str}', '{r['symbol']}', "
                f"{r['bid']}, {r['ask']}, {r['price']}, {r['spread']}, "
                f"{r['volume']}, {r['bid_volume']}, {r['ask_volume']}, "
                f"{r['hour_of_day']}, {r['day_of_week']}, '{r['trading_session']}', "
                f"{r['market_open']})"
            )
        
        # Insert in very small chunks to avoid QuestDB query size limits
        # QuestDB has shown connection issues with large queries
        chunk_size = 10  # Must be very small to avoid connection resets
        success = True
        
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i + chunk_size]
            query = f"""
            INSERT INTO market_data_v2 VALUES {', '.join(chunk)};
            """
            
            # Retry logic for connection issues
            max_retries = 3
            for retry in range(max_retries):
                try:
                    result = self.execute_query(query)
                    if result is not None:
                        break
                    time.sleep(0.1 * (retry + 1))  # Exponential backoff
                except Exception as e:
                    self.logger.warning(f"Retry {retry+1}/{max_retries} after error: {e}")
                    time.sleep(0.1 * (retry + 1))
            
            if retry == max_retries - 1 and result is None:
                self.logger.error(f"Failed to insert chunk after {max_retries} retries")
                success = False
        
        return success
    
    def insert_batch_ilp(self, records: List[Dict]) -> bool:
        """Insert batch of records using ILP protocol via Go ingestion service"""
        if not records:
            return True
        
        try:
            # Format timestamps properly for Go's time parser
            json_records = []
            for r in records:
                record = r.copy()
                # Convert timestamp to RFC3339 format with Z suffix (UTC)
                record['timestamp'] = r['timestamp'].strftime("%Y-%m-%dT%H:%M:%SZ")
                json_records.append(record)
            
            # Path to Go ingestion binary
            ingestion_binary = "/tmp/test_ilp"
            
            # Launch Go ingestion service with Python mode
            process = subprocess.Popen(
                [ingestion_binary, "-python"],
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send JSON data to the process
            json_data = json.dumps(json_records).encode('utf-8')
            stdout, stderr = process.communicate(input=json_data, timeout=self.request_timeout)
            
            # Check for errors
            if process.returncode != 0:
                stderr_text = stderr.decode()
                self.logger.error(f"ILP import failed via Go service: {stderr_text}")
                return False
            
            self.logger.info(f"Successfully inserted {len(records)} ticks via Go ILP service")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending data via Go ILP service: {e}")
            return False
    
    def insert_batch(self, records: List[Dict]) -> bool:
        """Insert batch of records using configured method"""
        if self.use_ilp:
            return self.insert_batch_ilp(records)
        else:
            return self.insert_batch_http(records)
    
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
    
    def generate_ohlcv(self, symbol: Optional[str] = None, timeframe: Optional[str] = None,
                      start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """
        Generate OHLCV data from tick data
        Can generate for specific symbol, timeframe, and date range
        """
        # Determine which timeframes to generate
        timeframes_to_generate = [timeframe] if timeframe else self.timeframes
        
        # Build the WHERE clause
        where_clauses = []
        if symbol:
            where_clauses.append(f"symbol = '{symbol}'")
        
        if start_date:
            where_clauses.append(f"timestamp >= '{start_date.isoformat()}'")
        
        if end_date:
            where_clauses.append(f"timestamp <= '{end_date.isoformat()}'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        where_sql = f"WHERE {where_clause}" if where_clause else ""
        
        # Generate OHLCV for each timeframe
        for tf in timeframes_to_generate:
            self.logger.info(f"Generating {tf} OHLCV data...")
            
            # For daily candles, use special query with proper calendar alignment
            if tf == '1d':
                query = f"""
                INSERT INTO ohlc_{tf}_v2
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
                {where_sql}
                SAMPLE BY {tf} ALIGN TO CALENDAR WITH OFFSET '00:00'
                """
            else:
                query = f"""
                INSERT INTO ohlc_{tf}_v2
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
                {where_sql}
                SAMPLE BY {tf} ALIGN TO CALENDAR
                """
            
            result = self.execute_query(query)
            if result:
                self.logger.info(f"Successfully generated {tf} OHLCV data")
            else:
                self.logger.error(f"Failed to generate {tf} OHLCV data")
    
    def download_date_range(self, instrument: str, start_date: datetime, end_date: datetime,
                           generate_ohlc: bool = False, verify: bool = False) -> int:
        """
        Download data for a date range using parallel processing
        Returns the total number of ticks loaded
        """
        self.logger.info(f"Downloading {instrument} from {start_date.date()} to {end_date.date()}")
        
        # Create batches of days to process
        batches = []
        current_start = start_date
        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=self.batch_days - 1), end_date)
            batches.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)
        
        self.logger.info(f"Split into {len(batches)} batches of {self.batch_days} days")
        
        # Process each batch
        total_ticks = 0
        failed_batches = []
        
        for batch_idx, (batch_start, batch_end) in enumerate(batches):
            # Check if this batch is already completed
            batch_key = f"{instrument}_{batch_start.date()}_{batch_end.date()}"
            if batch_key in self.state.get('completed_batches', []):
                self.logger.info(f"Skipping completed batch {batch_idx+1}/{len(batches)}: "
                                f"{batch_start.date()} to {batch_end.date()}")
                continue
            
            self.logger.info(f"Processing batch {batch_idx+1}/{len(batches)}: "
                            f"{batch_start.date()} to {batch_end.date()}")
            
            # Generate list of all hours to download in this batch
            tasks = []
            current = batch_start
            while current <= batch_end:
                # Skip weekends (market closed on Sat, Sun morning)
                weekday = current.weekday()
                if weekday < 5 or (weekday == 6 and current.hour >= 22):
                    for hour in range(24):
                        tasks.append((instrument, current, hour))
                current += timedelta(days=1)
            
            self.logger.info(f"Batch has {len(tasks)} hours to process")
            
            # Process in parallel
            processed_count = 0
            error_count = 0
            batch_ticks = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
                            batch_ticks += tick_count
                            
                            if processed_count % 10 == 0:
                                self.logger.info(f"Batch progress: {processed_count}/{len(tasks)} hours, "
                                               f"{batch_ticks:,} ticks")
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"Error processing {task}: {e}")
            
            # Update batch status
            if error_count == 0:
                if 'completed_batches' not in self.state:
                    self.state['completed_batches'] = []
                self.state['completed_batches'].append(batch_key)
                self.save_state()
                self.logger.info(f"Batch completed: {batch_ticks:,} ticks")
            else:
                failed_batches.append((batch_idx, batch_start, batch_end))
                self.logger.warning(f"Batch had {error_count} errors")
            
            total_ticks += batch_ticks
        
        # Report overall status
        self.logger.info(f"Download completed for {instrument}: {total_ticks:,} total ticks")
        if failed_batches:
            self.logger.warning(f"{len(failed_batches)} batches had errors:")
            for idx, start, end in failed_batches:
                self.logger.warning(f"  Batch {idx+1}: {start.date()} to {end.date()}")
        
        # Generate OHLC if requested
        if generate_ohlc and total_ticks > 0:
            self.logger.info("Generating OHLC data...")
            self.generate_ohlcv(instrument, None, start_date, end_date)
        
        # Verify data if requested
        if verify and total_ticks > 0:
            self.logger.info("Verifying data integrity...")
            self.verify_data_integrity(instrument, start_date, end_date)
        
        return total_ticks
    
    def download_latest(self, symbols: List[str], days: int = 1, 
                       generate_ohlc: bool = True, verify: bool = True) -> Dict[str, int]:
        """
        Download the latest data for multiple symbols
        Returns a dictionary of symbol -> tick count
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        results = {}
        for symbol in symbols:
            self.logger.info(f"Downloading latest data for {symbol}")
            tick_count = self.download_date_range(
                symbol, start_date, end_date, generate_ohlc=False, verify=False
            )
            results[symbol] = tick_count
        
        # Generate OHLC after all symbols are downloaded
        if generate_ohlc:
            self.logger.info("Generating OHLC data for all symbols...")
            self.generate_ohlcv(None, None, start_date, end_date)
        
        # Verify after all processing is done
        if verify:
            self.logger.info("Verifying data integrity for all symbols...")
            for symbol in symbols:
                self.verify_data_integrity(symbol, start_date, end_date)
        
        return results
    
    def verify_data_integrity(self, symbol: Optional[str] = None, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> bool:
        """
        Verify data integrity for a symbol and date range
        Checks for data gaps and OHLC consistency
        """
        # Build the WHERE clause
        where_clauses = []
        if symbol:
            where_clauses.append(f"symbol = '{symbol}'")
        
        if start_date:
            where_clauses.append(f"timestamp >= '{start_date.isoformat()}'")
        
        if end_date:
            where_clauses.append(f"timestamp <= '{end_date.isoformat()}'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        where_sql = f"WHERE {where_clause}" if where_clause else ""
        
        # Check for empty prices or spreads
        self.logger.info("Checking for invalid prices...")
        invalid_query = f"""
        SELECT count(*) 
        FROM market_data_v2 
        {where_sql} 
        AND (bid <= 0 OR ask <= 0 OR bid >= ask)
        """
        
        result = self.execute_query(invalid_query)
        if result and 'dataset' in result and len(result['dataset']) > 0:
            invalid_count = result['dataset'][0][0]
            if invalid_count > 0:
                self.logger.warning(f"Found {invalid_count} records with invalid prices")
            else:
                self.logger.info("No invalid prices found")
        
        # Check OHLC consistency for each timeframe
        all_valid = True
        for tf in self.timeframes:
            self.logger.info(f"Checking {tf} OHLC consistency...")
            
            # Check for OHLC candles with zero tick count
            zero_query = f"""
            SELECT count(*) 
            FROM ohlc_{tf}_v2 
            {where_sql} 
            AND tick_count = 0
            """
            
            result = self.execute_query(zero_query)
            if result and 'dataset' in result and len(result['dataset']) > 0:
                zero_count = result['dataset'][0][0]
                if zero_count > 0:
                    self.logger.warning(f"Found {zero_count} {tf} candles with zero ticks")
                    all_valid = False
                else:
                    self.logger.info(f"All {tf} candles have tick data")
            
            # Check for OHLC anomalies (high < low, close outside range, etc)
            anomaly_query = f"""
            SELECT count(*) 
            FROM ohlc_{tf}_v2 
            {where_sql} 
            AND (high < low OR close > high OR close < low OR open > high OR open < low)
            """
            
            result = self.execute_query(anomaly_query)
            if result and 'dataset' in result and len(result['dataset']) > 0:
                anomaly_count = result['dataset'][0][0]
                if anomaly_count > 0:
                    self.logger.warning(f"Found {anomaly_count} {tf} candles with price anomalies")
                    all_valid = False
                else:
                    self.logger.info(f"All {tf} candles have consistent prices")
        
        if all_valid:
            self.logger.info("Data verification complete: No issues found")
        else:
            self.logger.warning("Data verification complete: Issues detected")
        
        return all_valid
    
    def get_data_summary(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """
        Get summary of downloaded data
        Returns information about tick and OHLC data
        """
        # Build WHERE clause
        where_sql = f"WHERE symbol = '{symbol}'" if symbol else ""
        
        # Get tick data summary
        tick_query = f"""
        SELECT 
            symbol,
            count(*) as tick_count,
            min(timestamp) as first_tick,
            max(timestamp) as last_tick,
            avg(spread) as avg_spread,
            sum(volume) as total_volume
        FROM market_data_v2
        {where_sql}
        GROUP BY symbol
        ORDER BY symbol
        """
        
        tick_result = self.execute_query(tick_query)
        if not tick_result or 'dataset' not in tick_result:
            self.logger.error("Failed to get tick data summary")
            return None
        
        # Get OHLC data summary for each timeframe
        ohlc_summary = {}
        for tf in self.timeframes:
            ohlc_query = f"""
            SELECT 
                symbol,
                count(*) as candle_count,
                min(timestamp) as first_candle,
                max(timestamp) as last_candle,
                avg(tick_count) as avg_ticks_per_candle
            FROM ohlc_{tf}_v2
            {where_sql}
            GROUP BY symbol
            ORDER BY symbol
            """
            
            ohlc_result = self.execute_query(ohlc_query)
            if ohlc_result and 'dataset' in ohlc_result:
                ohlc_summary[tf] = ohlc_result['dataset']
        
        # Format results
        summary = {
            'tick_data': tick_result['dataset'],
            'ohlc_data': ohlc_summary
        }
        
        return summary
    
    def print_data_summary(self, summary: Dict):
        """Print data summary in a formatted way"""
        if not summary:
            print("No data available")
            return
        
        # Print tick data summary
        print("\n📊 Tick Data Summary:")
        print(f"{'Symbol':<10} {'Ticks':<15} {'First':<20} {'Last':<20} {'Avg Spread':<12} {'Total Volume':<15}")
        print("-" * 100)
        
        for row in summary['tick_data']:
            symbol, ticks, first, last, spread, volume = row
            print(f"{symbol:<10} {ticks:<15,} {first:<20} {last:<20} {spread:<12.5f} {volume:<15,.2f}")
        
        # Print OHLC data summary for each timeframe
        for tf, data in summary['ohlc_data'].items():
            print(f"\n📈 {tf} OHLC Summary:")
            print(f"{'Symbol':<10} {'Candles':<15} {'First':<20} {'Last':<20} {'Avg Ticks/Candle':<20}")
            print("-" * 85)
            
            for row in data:
                symbol, count, first, last, avg_ticks = row
                print(f"{symbol:<10} {count:<15,} {first:<20} {last:<20} {avg_ticks:<20.2f}")
    
    def interactive_mode(self):
        """Run in interactive mode with a menu"""
        while True:
            print("\n🔧 Dukascopy Data Manager")
            print("-" * 40)
            print("1. Download latest data (last 24 hours)")
            print("2. Download custom date range")
            print("3. Generate OHLC data")
            print("4. Verify data integrity")
            print("5. Show data summary")
            print("6. Create/update database tables")
            print("0. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            
            elif choice == '1':
                # Latest data
                symbols_str = input(f"Symbols (comma-separated, default: {','.join(self.symbols)}): ").strip()
                symbols = [s.strip().upper() for s in symbols_str.split(',')] if symbols_str else self.symbols
                
                generate_ohlc = input("Generate OHLC candles? (y/n, default: y): ").strip().lower() != 'n'
                verify = input("Verify data integrity? (y/n, default: y): ").strip().lower() != 'n'
                
                results = self.download_latest(symbols, days=1, generate_ohlc=generate_ohlc, verify=verify)
                
                print("\nDownload results:")
                for symbol, count in results.items():
                    print(f"{symbol}: {count:,} ticks")
            
            elif choice == '2':
                # Custom date range
                symbol = input("Symbol (e.g., EURUSD): ").strip().upper()
                if not symbol:
                    print("Symbol is required")
                    continue
                
                start_str = input("Start date (YYYY-MM-DD): ").strip()
                end_str = input("End date (YYYY-MM-DD, default: today): ").strip()
                
                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) if end_str else datetime.now(timezone.utc)
                    
                    generate_ohlc = input("Generate OHLC candles? (y/n, default: y): ").strip().lower() != 'n'
                    verify = input("Verify data integrity? (y/n, default: y): ").strip().lower() != 'n'
                    
                    tick_count = self.download_date_range(
                        symbol, start_date, end_date, generate_ohlc=generate_ohlc, verify=verify
                    )
                    
                    print(f"\nDownloaded {tick_count:,} ticks for {symbol}")
                    
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            elif choice == '3':
                # Generate OHLC
                symbol = input("Symbol (leave empty for all symbols): ").strip().upper()
                tf = input("Timeframe (leave empty for all timeframes): ").strip().lower()
                
                start_str = input("Start date (YYYY-MM-DD, optional): ").strip()
                end_str = input("End date (YYYY-MM-DD, optional): ").strip()
                
                start_date = None
                end_date = None
                
                if start_str:
                    try:
                        start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"Invalid start date: {e}")
                        continue
                
                if end_str:
                    try:
                        end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"Invalid end date: {e}")
                        continue
                
                self.generate_ohlcv(
                    symbol if symbol else None,
                    tf if tf else None,
                    start_date,
                    end_date
                )
                
                print("OHLC generation complete")
            
            elif choice == '4':
                # Verify data
                symbol = input("Symbol (leave empty for all symbols): ").strip().upper()
                
                start_str = input("Start date (YYYY-MM-DD, optional): ").strip()
                end_str = input("End date (YYYY-MM-DD, optional): ").strip()
                
                start_date = None
                end_date = None
                
                if start_str:
                    try:
                        start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"Invalid start date: {e}")
                        continue
                
                if end_str:
                    try:
                        end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"Invalid end date: {e}")
                        continue
                
                self.verify_data_integrity(
                    symbol if symbol else None,
                    start_date,
                    end_date
                )
            
            elif choice == '5':
                # Data summary
                symbol = input("Symbol (leave empty for all symbols): ").strip().upper()
                
                summary = self.get_data_summary(symbol if symbol else None)
                self.print_data_summary(summary)
            
            elif choice == '6':
                # Create tables
                self.create_database_tables()
                print("Database tables created/updated")
            
            else:
                print("Invalid choice")


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime with UTC timezone"""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Dukascopy Data Downloader and Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download data for a specific symbol and date range
  python download_and_import.py download EURUSD 2024-01-01 2024-01-07

  # Download yesterday's data for all configured symbols
  python download_and_import.py daily

  # Generate OHLC data only (no download)
  python download_and_import.py ohlc EURUSD 2024-01-01 2024-01-07

  # Check data integrity
  python download_and_import.py verify

  # Get data summary
  python download_and_import.py summary

  # Interactive mode
  python download_and_import.py interactive
        """
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # 1. Download command - download specific date range for a symbol
    download_parser = subparsers.add_parser(
        "download", help="Download data for a specific symbol and date range"
    )
    download_parser.add_argument("symbol", help="Symbol to download (e.g., EURUSD)")
    download_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    download_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    download_parser.add_argument(
        "--batch-days", type=int, help="Number of days to process in each batch"
    )
    download_parser.add_argument(
        "--generate-ohlc", action="store_true", help="Generate OHLC candles after downloading"
    )
    download_parser.add_argument(
        "--verify", action="store_true", help="Verify data integrity after downloading"
    )
    
    # 2. Daily command - download yesterday's data for all symbols
    daily_parser = subparsers.add_parser(
        "daily", help="Download yesterday's data for all configured symbols"
    )
    daily_parser.add_argument(
        "--symbols", nargs="+", help="Symbols to download (default: from config.yaml)"
    )
    daily_parser.add_argument(
        "--generate-ohlc", action="store_true", help="Generate OHLC candles after downloading"
    )
    daily_parser.add_argument(
        "--verify", action="store_true", help="Verify data integrity after downloading"
    )
    daily_parser.add_argument(
        "--days", type=int, default=1, help="Number of days to download (default: 1)"
    )
    
    # 3. OHLC command - generate OHLC data from existing tick data
    ohlc_parser = subparsers.add_parser(
        "ohlc", help="Generate OHLC candles from existing tick data"
    )
    ohlc_parser.add_argument("symbol", help="Symbol to process (e.g., EURUSD)")
    ohlc_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    ohlc_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    ohlc_parser.add_argument(
        "--timeframe", help="Specific timeframe to generate (default: all from config)"
    )
    
    # 4. Verify command - verify data integrity
    verify_parser = subparsers.add_parser(
        "verify", help="Verify data integrity"
    )
    verify_parser.add_argument(
        "--symbol", help="Symbol to verify (default: all symbols)"
    )
    verify_parser.add_argument(
        "--start-date", help="Start date (YYYY-MM-DD)"
    )
    verify_parser.add_argument(
        "--end-date", help="End date (YYYY-MM-DD)"
    )
    
    # 5. Summary command - get data summary
    summary_parser = subparsers.add_parser(
        "summary", help="Get data summary"
    )
    summary_parser.add_argument(
        "--symbol", help="Symbol to summarize (default: all symbols)"
    )
    
    # 6. Setup command - create database tables
    setup_parser = subparsers.add_parser(
        "setup", help="Set up database tables"
    )
    
    # 7. Interactive command - run in interactive mode
    interactive_parser = subparsers.add_parser(
        "interactive", help="Run in interactive mode"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create manager
    manager = DukascopyManager()
    
    # Execute command
    if args.command == "download":
        # Override batch_days if provided
        if args.batch_days:
            manager.batch_days = args.batch_days
        
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
        
        manager.download_date_range(
            args.symbol, start_date, end_date, 
            generate_ohlc=args.generate_ohlc,
            verify=args.verify
        )
    
    elif args.command == "daily":
        symbols = args.symbols if args.symbols else manager.symbols
        manager.download_latest(
            symbols, days=args.days,
            generate_ohlc=args.generate_ohlc,
            verify=args.verify
        )
    
    elif args.command == "ohlc":
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
        
        manager.generate_ohlcv(
            args.symbol, args.timeframe, start_date, end_date
        )
    
    elif args.command == "verify":
        start_date = parse_date(args.start_date) if args.start_date else None
        end_date = parse_date(args.end_date) if args.end_date else None
        
        manager.verify_data_integrity(args.symbol, start_date, end_date)
    
    elif args.command == "summary":
        summary = manager.get_data_summary(args.symbol)
        manager.print_data_summary(summary)
    
    elif args.command == "setup":
        manager.create_database_tables()
        print("Database tables created/updated")
    
    elif args.command == "interactive":
        manager.interactive_mode()
    
    else:
        # Default to interactive mode if no command
        manager.interactive_mode()


if __name__ == "__main__":
    main()