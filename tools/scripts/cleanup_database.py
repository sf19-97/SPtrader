#!/usr/bin/env python3
"""
Database Cleanup Script
Prepares database for verified OHLC generation
*Created: May 31, 2025*
"""

import requests
import sys
import logging
import time
from datetime import datetime

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/db_cleanup.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DatabaseCleanup")

def execute_query(query, silent=False):
    """Execute a query against QuestDB with error handling"""
    if not silent:
        logger.info(f"Executing query: {query[:100]}..." if len(query) > 100 else f"Executing query: {query}")
    
    try:
        response = requests.get(QUESTDB_URL, params={'query': query})
        if response.status_code != 200:
            logger.error(f"Query failed with status {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        if 'error' in result:
            logger.error(f"Query error: {result['error']}")
            return None
        
        if not silent:
            logger.info("✅ Query executed successfully")
        
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None

def backup_table(table_name):
    """Create a backup of a table if it exists"""
    # Check if table exists
    check_query = f"SELECT count(*) FROM {table_name} LIMIT 1"
    result = execute_query(check_query, silent=True)
    
    if not result:
        logger.info(f"Table {table_name} does not exist or is empty, skipping backup")
        return True
    
    # Create backup
    backup_table = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_query = f"""
    CREATE TABLE IF NOT EXISTS {backup_table} AS (
        SELECT * FROM {table_name}
    )
    """
    
    result = execute_query(backup_query)
    if not result:
        logger.error(f"❌ Failed to create backup of {table_name}")
        return False
    
    # Count rows in backup
    count_query = f"SELECT COUNT(*) FROM {backup_table}"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset']:
        count = result['dataset'][0][0]
        logger.info(f"✅ Backup created: {backup_table} with {count:,} rows")
    
    return True

def drop_ohlc_tables():
    """Drop all OHLC tables after backing them up"""
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    success = True
    
    # Back up raw tick data first
    logger.info("Creating backup of raw tick data...")
    if not backup_table("market_data_v2"):
        logger.error("❌ Failed to backup raw tick data, aborting cleanup")
        return False
    
    # Process each OHLC table
    for tf in timeframes:
        table_name = f"ohlc_{tf}_v2"
        logger.info(f"Processing {table_name}...")
        
        # Backup table
        if not backup_table(table_name):
            logger.warning(f"⚠️ Could not backup {table_name}, but continuing...")
        
        # Drop table
        drop_query = f"DROP TABLE IF EXISTS {table_name}"
        logger.info(f"Dropping table {table_name}...")
        if not execute_query(drop_query):
            logger.error(f"❌ Failed to drop {table_name}")
            success = False
        else:
            logger.info(f"✅ Successfully dropped {table_name}")
    
    if success:
        logger.info("✅ All OHLC tables dropped successfully")
    else:
        logger.error("❌ Some errors occurred during table cleanup")
    
    return success

def main():
    """Main function"""
    logger.info("=== Database Cleanup Started ===")
    
    try:
        # Verify QuestDB connection
        test_query = "SELECT 1"
        result = execute_query(test_query)
        if not result:
            logger.error("❌ QuestDB connection failed, aborting cleanup")
            sys.exit(1)
        
        # Check for command-line flag to bypass confirmation
        if len(sys.argv) > 1 and sys.argv[1] == "--force":
            logger.info("Force flag detected, skipping confirmation")
            confirmation = "YES"
        else:
            # Ask for confirmation
            print("\n⚠️  WARNING: This script will drop all OHLC tables after backing them up.")
            print("      It is intended to be run before generating new verified OHLC data.")
            confirmation = input("\nType 'YES' to confirm: ")
        
        if confirmation != "YES":
            print("Operation cancelled by user.")
            sys.exit(0)
        
        # Perform cleanup
        start_time = time.time()
        if drop_ohlc_tables():
            elapsed_time = time.time() - start_time
            logger.info(f"=== Database Cleanup Completed in {elapsed_time:.2f} seconds ===")
            logger.info("You can now run verified_ohlc_generator.py to create new OHLC data")
        else:
            logger.error("❌ Database cleanup failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Error during database cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()