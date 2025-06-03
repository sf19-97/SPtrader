#!/usr/bin/env python3
"""
Daily Update Script (VERIFIED)
Safe and verified version of the daily update process
*Created: May 31, 2025*
"""

import os
import sys
import subprocess
import logging
import time
import datetime
from datetime import datetime, timedelta

# Configuration
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/daily_update.log"
SCRIPTS_DIR = "/home/millet_frazier/SPtrader/tools/scripts"
DATA_FEEDS_DIR = "/home/millet_frazier/SPtrader/tools/data-feeds"

# Default symbols to process
DEFAULT_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DailyUpdateVerified")

def run_command(cmd, description):
    """Run a shell command and log the output"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {cmd}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True)
        elapsed_time = time.time() - start_time
        
        logger.info(f"✅ {description} completed in {elapsed_time:.2f} seconds")
        logger.info(f"Output: {result.stdout[:500]}..." if len(result.stdout) > 500 else f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def download_data(symbol, start_date, end_date):
    """Download data for a symbol for a date range"""
    cmd = f"cd {DATA_FEEDS_DIR} && python3 dukascopy_loader.py load {symbol} {start_date} {end_date}"
    return run_command(cmd, f"Downloading {symbol} data for {start_date} to {end_date}")

def generate_ohlc(symbol):
    """Generate OHLC data for a symbol using verified generator"""
    cmd = f"cd {SCRIPTS_DIR} && python3 verified_ohlc_generator.py {symbol}"
    return run_command(cmd, f"Generating verified OHLC data for {symbol}")

def main():
    """Main function"""
    logger.info("=== Daily Update (VERIFIED) Started ===")
    
    try:
        # Get symbols from command line or use defaults
        symbols = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SYMBOLS
        
        # Calculate date range (yesterday to today)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        logger.info(f"Processing symbols: {', '.join(symbols)}")
        logger.info(f"Date range: {yesterday} to {today}")
        
        # Process each symbol
        for symbol in symbols:
            logger.info(f"=== Processing {symbol} ===")
            
            # 1. Download latest data
            if not download_data(symbol, yesterday, today):
                logger.error(f"❌ Failed to download data for {symbol}, skipping OHLC generation")
                continue
            
            # 2. Generate OHLC data
            if not generate_ohlc(symbol):
                logger.error(f"❌ Failed to generate OHLC data for {symbol}")
                continue
            
            logger.info(f"✅ {symbol} processing completed successfully")
        
        logger.info("=== Daily Update (VERIFIED) Completed ===")
    
    except Exception as e:
        logger.error(f"❌ Error during daily update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()