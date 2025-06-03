#!/usr/bin/env python3
"""
Tick Data Purge Script
Removes all tick data from the database
*Created: May 31, 2025*
"""

import requests
import logging
import sys

# Configuration
QUESTDB_URL = "http://localhost:9000/exec"
LOG_FILE = "/home/millet_frazier/SPtrader/logs/runtime/purge_tick_data.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TickDataPurge")

def execute_query(query):
    """Execute a query against QuestDB with error handling"""
    logger.info(f"Executing query: {query}")
    
    try:
        response = requests.get(QUESTDB_URL, params={'query': query})
        if response.status_code != 200:
            logger.error(f"Query failed with status {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        if 'error' in result:
            logger.error(f"Query error: {result['error']}")
            return None
        
        logger.info("✅ Query executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None

def purge_all_data():
    """Purge all market data and OHLC tables"""
    logger.info("=== Starting complete data purge ===")
    
    # 1. Drop market data tables
    tables = [
        "market_data_v2",       # Main tick data table
        "ohlc_1m_v2",           # OHLC tables
        "ohlc_5m_v2",
        "ohlc_15m_v2",
        "ohlc_30m_v2",
        "ohlc_1h_v2",
        "ohlc_4h_v2",
        "ohlc_1d_v2"
    ]
    
    for table in tables:
        query = f"DROP TABLE IF EXISTS {table}"
        result = execute_query(query)
        if result:
            logger.info(f"✅ Table {table} dropped successfully")
        else:
            logger.error(f"❌ Failed to drop table {table}")
            return False
    
    # 2. Recreate market_data_v2 table as empty
    create_query = """
    CREATE TABLE market_data_v2 (
        timestamp TIMESTAMP,
        symbol SYMBOL,
        price DOUBLE,
        volume DOUBLE,
        source SYMBOL
    ) TIMESTAMP(timestamp) PARTITION BY DAY;
    """
    
    result = execute_query(create_query)
    if result:
        logger.info("✅ Empty market_data_v2 table created")
    else:
        logger.error("❌ Failed to create empty market_data_v2 table")
        return False
    
    # 3. Verify tables are empty
    count_query = "SELECT COUNT(*) FROM market_data_v2"
    result = execute_query(count_query)
    if result and 'dataset' in result and result['dataset'] and result['dataset'][0][0] == 0:
        logger.info("✅ Verified market_data_v2 is empty")
    else:
        logger.error("❌ Failed to verify market_data_v2 is empty")
        return False
    
    logger.info("=== Data purge completed successfully ===")
    logger.info("All tick data and OHLC tables have been removed.")
    logger.info("The system is now in a clean state with zero data.")
    return True

def main():
    logger.info("WARNING: This script will remove ALL market data and OHLC tables!")
    logger.info("This action CANNOT be undone.")
    
    # Get confirmation from command line
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        confirm = "y"
    else:
        confirm = input("Are you sure you want to purge ALL data? (y/n): ")
    
    if confirm.lower() != "y":
        logger.info("Operation cancelled.")
        return
    
    # Run purge operation
    if purge_all_data():
        logger.info("✅ All data successfully purged")
    else:
        logger.error("❌ Data purge failed")
        sys.exit(1)

if __name__ == "__main__":
    main()