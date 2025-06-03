#!/usr/bin/env python3
"""
Unified Dukascopy Data Loader
A single tool for all Dukascopy data loading operations
*Created: May 31, 2025*
"""

import sys
import json
import subprocess
import argparse
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure dukascopy_importer is in the path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

try:
    from dukascopy_importer import DukascopyDownloader
except ImportError:
    print("Error: Unable to import DukascopyDownloader. Make sure dukascopy_importer.py is in the same directory.")
    sys.exit(1)

# Configuration
STATE_FILE = os.path.join(SCRIPT_DIR, ".batch_progress.json")
DEFAULT_BATCH_DAYS = 3
INGESTION_BINARY = "/home/millet_frazier/SPtrader/cmd/bin/ingestion"
LOG_DIR = "/home/millet_frazier/SPtrader/logs/runtime"
os.makedirs(LOG_DIR, exist_ok=True)

# Initialize downloader globally so it can be reused
downloader = DukascopyDownloader()

def setup_logger(symbol, start_date, end_date):
    """Set up logging"""
    import logging
    log_file = os.path.join(LOG_DIR, f"dukascopy_loader_{symbol}_{start_date}_{end_date}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("DukascopyLoader")

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

def send_to_ilp(records, logger):
    """Send batch of records to ILP ingestion"""
    if not records:
        return True
    
    logger.info(f"📤 Sending {len(records):,} ticks to ILP...")
    
    # Convert to JSON and pipe to Go ingestion service
    json_data = json.dumps(records, default=str)
    
    # Run the Go ingestion service
    process = subprocess.Popen(
        [INGESTION_BINARY, '-python'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Send data and get output
    output, _ = process.communicate(input=json_data)
    
    if process.returncode == 0:
        logger.info(f"✅ Batch successfully ingested!")
        return True
    else:
        logger.error(f"❌ Ingestion failed: {output}")
        return False

def download_single_day(symbol, date, logger):
    """Download and process a single day of data"""
    logger.info(f"📅 Processing {symbol} for {date.date()}")
    
    all_records = []
    
    # Process each hour of the day
    for hour in range(24):
        try:
            # Download hour data
            data = downloader.download_hour_data(symbol, date, hour)
            if data:
                # Process into records
                records = downloader.process_hour_ticks(symbol, date, hour, data)
                if records:
                    all_records.extend(records)
                    logger.info(f"  ✅ Hour {hour:02d}: {len(records)} ticks")
                else:
                    logger.info(f"  ℹ️ Hour {hour:02d}: No ticks found")
            else:
                logger.info(f"  ℹ️ Hour {hour:02d}: No data found")
        except Exception as e:
            logger.error(f"  ❌ Hour {hour:02d}: Error: {str(e)}")
    
    logger.info(f"✅ Downloaded {len(all_records):,} ticks for {date.date()}")
    return all_records

def process_date_range(symbol, start_date, end_date, batch_days, logger):
    """Process a date range in batches"""
    # Load progress
    progress = load_progress()
    job_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
    
    if job_key in progress:
        last_processed = datetime.fromisoformat(progress[job_key]).replace(tzinfo=timezone.utc)
        logger.info(f"📂 Resuming from {last_processed.date()}...")
        current = last_processed + timedelta(days=1)
    else:
        current = start_date
        logger.info(f"📊 Starting batch download of {symbol} from {start_date.date()} to {end_date.date()}...")
    
    # Process in batches
    total_ticks = 0
    failed_batches = []
    
    while current <= end_date:
        # Calculate batch end (up to batch_days or end_date)
        batch_end = min(current + timedelta(days=batch_days - 1), end_date)
        
        logger.info(f"\n🔄 Processing batch: {current.date()} to {batch_end.date()}")
        
        try:
            # Download data for each day in the batch
            batch_records = []
            batch_current = current
            
            # First pre-download the data range
            logger.info(f"  📥 Pre-downloading data range...")
            downloader.download_date_range([symbol], batch_current, batch_end)
            
            # Process each day in the batch
            while batch_current <= batch_end:
                day_records = download_single_day(symbol, batch_current, logger)
                batch_records.extend(day_records)
                batch_current = batch_current.replace(hour=0) + timedelta(days=1)
            
            logger.info(f"  📊 Total batch: {len(batch_records):,} ticks")
            
            # Send batch to ILP
            if batch_records:
                if send_to_ilp(batch_records, logger):
                    total_ticks += len(batch_records)
                    # Update progress
                    progress[job_key] = batch_end.isoformat()
                    save_progress(progress)
                else:
                    failed_batches.append((current.date(), batch_end.date()))
                    logger.warning(f"  ⚠️  Failed to ingest batch {current.date()} to {batch_end.date()}")
            
            # Clear memory
            batch_records = None
            
        except Exception as e:
            logger.error(f"  ❌ Error processing batch: {e}")
            failed_batches.append((current.date(), batch_end.date()))
        
        # Move to next batch
        current = batch_end + timedelta(days=1)
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Total ticks ingested: {total_ticks:,}")
    
    if failed_batches:
        logger.warning(f"\n⚠️  Failed batches ({len(failed_batches)}):")
        for start, end in failed_batches:
            logger.warning(f"   - {start} to {end}")
        logger.info("\nYou can re-run the script to retry failed batches.")
    else:
        logger.info("✅ All batches processed successfully!")
        # Clean up progress for this job
        if job_key in progress:
            del progress[job_key]
            save_progress(progress)
    
    # Check database
    logger.info("\n📊 Checking database...")
    check_cmd = f'sptrader db query "SELECT COUNT(*) FROM market_data_v2 WHERE symbol = \'{symbol}\' AND timestamp >= \'{start_date.date()}\'"'
    os.system(check_cmd)
    
    return total_ticks, failed_batches

def process_yesterday(symbols, logger):
    """Process yesterday's data for all specified symbols"""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    today = yesterday + timedelta(days=1)
    
    logger.info(f"📅 Processing data for period: {yesterday.date()} to {today.date()}")
    
    results = {}
    for symbol in symbols:
        logger.info(f"\n🔄 Processing {symbol}...")
        try:
            total_ticks, failed_batches = process_date_range(symbol, yesterday, yesterday, 1, logger)
            results[symbol] = {"ticks": total_ticks, "failed": len(failed_batches) > 0}
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
            results[symbol] = {"ticks": 0, "failed": True}
    
    return results

def generate_ohlc(symbols, start_date, end_date, logger):
    """Generate OHLC candles for all symbols and specified date range"""
    logger.info(f"📊 Generating OHLC candles...")
    
    for symbol in symbols:
        logger.info(f"\n🔄 Generating OHLC candles for {symbol}...")
        
        # Call production_ohlc_generator.py
        try:
            cmd = [
                "python3", 
                os.path.join(SCRIPT_DIR, "..", "scripts", "production_ohlc_generator.py"),
                symbol,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully generated OHLC candles for {symbol}")
                logger.info(result.stdout.strip())
            else:
                logger.error(f"❌ Failed to generate OHLC candles for {symbol}")
                logger.error(result.stderr.strip())
        
        except Exception as e:
            logger.error(f"❌ Error generating OHLC candles for {symbol}: {e}")

def verify_data(symbols, logger):
    """Verify data integrity for all specified symbols"""
    logger.info(f"🔍 Verifying data integrity...")
    
    try:
        cmd = [
            "python3", 
            os.path.join(SCRIPT_DIR, "..", "scripts", "monitor_ohlc_integrity.py")
        ]
        if symbols:
            for symbol in symbols:
                cmd.extend(["-s", symbol])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Data verification passed")
            logger.info(result.stdout.strip())
        else:
            logger.error(f"❌ Data verification failed")
            logger.error(result.stderr.strip())
    
    except Exception as e:
        logger.error(f"❌ Error during data verification: {e}")

def main():
    parser = argparse.ArgumentParser(description="Unified Dukascopy Data Loader")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # 1. Load command - load specific date range for a symbol
    load_parser = subparsers.add_parser("load", help="Load data for a specific symbol and date range")
    load_parser.add_argument("symbol", help="Symbol to load (e.g., EURUSD)")
    load_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    load_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    load_parser.add_argument("--batch-days", type=int, default=DEFAULT_BATCH_DAYS, 
                            help=f"Number of days to process in each batch (default: {DEFAULT_BATCH_DAYS})")
    load_parser.add_argument("--generate-ohlc", action="store_true", 
                            help="Also generate OHLC candles after loading")
    load_parser.add_argument("--verify", action="store_true", 
                            help="Verify data integrity after loading")
    
    # 2. Daily command - load yesterday's data for all symbols
    daily_parser = subparsers.add_parser("daily", help="Load yesterday's data for specified symbols")
    daily_parser.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD", "USDJPY"], 
                             help="Symbols to load (default: EURUSD GBPUSD USDJPY)")
    daily_parser.add_argument("--generate-ohlc", action="store_true", 
                             help="Also generate OHLC candles after loading")
    daily_parser.add_argument("--verify", action="store_true", 
                             help="Verify data integrity after loading")
    
    # 3. OHLC command - just generate OHLC candles for existing data
    ohlc_parser = subparsers.add_parser("ohlc", help="Generate OHLC candles for existing data")
    ohlc_parser.add_argument("symbol", help="Symbol to process (e.g., EURUSD)")
    ohlc_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    ohlc_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    
    # 4. Verify command - just verify data integrity
    verify_parser = subparsers.add_parser("verify", help="Verify data integrity")
    verify_parser.add_argument("--symbols", nargs="+", 
                              help="Symbols to verify (default: all symbols)")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Process commands
    if args.command == "load":
        # Parse dates
        try:
            start_date = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD.")
            return
        
        # Set up logger
        logger = setup_logger(args.symbol, args.start_date, args.end_date)
        
        # Log start
        logger.info(f"=== Starting Dukascopy data load ===")
        logger.info(f"Symbol: {args.symbol}")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Batch size: {args.batch_days} days")
        
        # Load data
        total_ticks, failed_batches = process_date_range(
            args.symbol, start_date, end_date, args.batch_days, logger
        )
        
        # Generate OHLC if requested
        if args.generate_ohlc:
            generate_ohlc([args.symbol], start_date, end_date, logger)
        
        # Verify data if requested
        if args.verify:
            verify_data([args.symbol], logger)
        
        # Log completion
        logger.info(f"=== Data load completed ===")
        logger.info(f"Total ticks: {total_ticks:,}")
        logger.info(f"Failed batches: {len(failed_batches)}")
    
    elif args.command == "daily":
        # Set up logger
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        logger = setup_logger("daily", yesterday, yesterday)
        
        # Log start
        logger.info(f"=== Starting daily data load ===")
        logger.info(f"Symbols: {', '.join(args.symbols)}")
        
        # Process yesterday's data
        results = process_yesterday(args.symbols, logger)
        
        # Generate OHLC if requested
        if args.generate_ohlc:
            yesterday_dt = datetime.now(timezone.utc) - timedelta(days=1)
            yesterday_dt = yesterday_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            today_dt = yesterday_dt + timedelta(days=1)
            generate_ohlc(args.symbols, yesterday_dt, today_dt, logger)
        
        # Verify data if requested
        if args.verify:
            verify_data(args.symbols, logger)
        
        # Log completion
        logger.info(f"=== Daily data load completed ===")
        for symbol, result in results.items():
            logger.info(f"{symbol}: {result['ticks']:,} ticks, {'Failed' if result['failed'] else 'Success'}")
    
    elif args.command == "ohlc":
        # Parse dates
        try:
            start_date = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD.")
            return
        
        # Set up logger
        logger = setup_logger(args.symbol + "_ohlc", args.start_date, args.end_date)
        
        # Log start
        logger.info(f"=== Starting OHLC generation ===")
        logger.info(f"Symbol: {args.symbol}")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        
        # Generate OHLC
        generate_ohlc([args.symbol], start_date, end_date, logger)
        
        # Log completion
        logger.info(f"=== OHLC generation completed ===")
    
    elif args.command == "verify":
        # Set up logger
        logger = setup_logger("verify", "all", "all")
        
        # Log start
        logger.info(f"=== Starting data verification ===")
        if args.symbols:
            logger.info(f"Symbols: {', '.join(args.symbols)}")
        else:
            logger.info(f"Symbols: All")
        
        # Verify data
        verify_data(args.symbols, logger)
        
        # Log completion
        logger.info(f"=== Data verification completed ===")

if __name__ == "__main__":
    main()