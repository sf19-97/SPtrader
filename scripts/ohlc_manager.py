#!/usr/bin/env python3
"""
Automated OHLC Table Maintenance Script
Continuously updates OHLC tables from raw market_data
"""

import requests
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OHLCManager:
    def __init__(self, questdb_url="http://localhost:9000"):
        self.questdb_url = questdb_url
        
        # OHLC timeframes to maintain
        self.timeframes = {
            '1m': '1m',
            '5m': '5m', 
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
    
    def execute_query(self, query):
        """Execute SQL query on QuestDB"""
        try:
            response = requests.get(f"{self.questdb_url}/exec", params={"query": query})
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Query failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def create_ohlc_tables(self):
        """Create OHLC tables for all timeframes"""
        for timeframe in self.timeframes:
            table_name = f"ohlc_{timeframe}"
            
            query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TIMESTAMP,
                symbol SYMBOL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                tick_count LONG,
                trading_session SYMBOL
            ) timestamp(timestamp) PARTITION BY DAY;
            """
            
            result = self.execute_query(query)
            if result:
                logger.info(f"Created/verified table: {table_name}")
            else:
                logger.error(f"Failed to create table: {table_name}")
    
    def get_last_candle_time(self, table_name):
        """Get the timestamp of the last candle in OHLC table"""
        query = f"SELECT max(timestamp) as last_time FROM {table_name};"
        
        result = self.execute_query(query)
        if result and result.get('dataset') and result['dataset'][0][0]:
            return result['dataset'][0][0]
        else:
            # If no data, start from 24 hours ago
            return (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
    
    def update_ohlc_table(self, timeframe):
        """Update OHLC table with new candles"""
        table_name = f"ohlc_{timeframe}"
        
        # Get last update time
        last_time = self.get_last_candle_time(table_name)
        
        # Generate new OHLC data from raw ticks
        query = f"""
        INSERT INTO {table_name}
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
        WHERE timestamp > '{last_time}'
        SAMPLE BY {timeframe} ALIGN TO CALENDAR
        ORDER BY timestamp;
        """
        
        result = self.execute_query(query)
        if result:
            logger.info(f"Updated {table_name} with new candles from {last_time}")
            
            # Count how many rows were inserted
            count_query = f"SELECT count(*) FROM {table_name} WHERE timestamp > '{last_time}';"
            count_result = self.execute_query(count_query)
            if count_result and count_result.get('dataset'):
                row_count = count_result['dataset'][0][0]
                logger.info(f"  → Inserted {row_count} new {timeframe} candles")
        else:
            logger.error(f"Failed to update {table_name}")
    
    def update_all_timeframes(self):
        """Update all OHLC timeframes"""
        logger.info("Starting OHLC update cycle...")
        
        for timeframe in self.timeframes:
            try:
                self.update_ohlc_table(timeframe)
            except Exception as e:
                logger.error(f"Error updating {timeframe}: {e}")
        
        logger.info("OHLC update cycle complete")
    
    def cleanup_old_data(self, days_to_keep=90):
        """Remove old OHLC data to save space"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat() + 'Z'
        
        for timeframe in self.timeframes:
            table_name = f"ohlc_{timeframe}"
            
            # Keep more data for smaller timeframes
            if timeframe in ['1m', '5m']:
                keep_days = 7  # 1 week for minute data
            elif timeframe in ['15m', '1h']:
                keep_days = 30  # 1 month for hourly data
            else:
                keep_days = days_to_keep  # 3 months for daily data
            
            cutoff = (datetime.utcnow() - timedelta(days=keep_days)).isoformat() + 'Z'
            
            query = f"DELETE FROM {table_name} WHERE timestamp < '{cutoff}';"
            result = self.execute_query(query)
            
            if result:
                logger.info(f"Cleaned old data from {table_name} (older than {keep_days} days)")
    
    def get_ohlc_stats(self):
        """Get statistics about OHLC tables"""
        logger.info("OHLC Table Statistics:")
        
        for timeframe in self.timeframes:
            table_name = f"ohlc_{timeframe}"
            
            query = f"""
            SELECT 
                count(*) as total_candles,
                count(DISTINCT symbol) as symbols,
                min(timestamp) as first_candle,
                max(timestamp) as last_candle
            FROM {table_name};
            """
            
            result = self.execute_query(query)
            if result and result.get('dataset'):
                data = result['dataset'][0]
                logger.info(f"  {table_name}: {data[0]} candles, {data[1]} symbols, {data[2]} to {data[3]}")
    
    def run_continuous(self, update_interval=60):
        """Run continuous OHLC maintenance"""
        logger.info(f"Starting continuous OHLC maintenance (every {update_interval}s)")
        
        # Initial setup
        self.create_ohlc_tables()
        
        while True:
            try:
                # Update all timeframes
                self.update_all_timeframes()
                
                # Show stats every 10 cycles
                if hasattr(self, 'cycle_count'):
                    self.cycle_count += 1
                else:
                    self.cycle_count = 1
                
                if self.cycle_count % 10 == 0:
                    self.get_ohlc_stats()
                
                # Cleanup old data every 100 cycles
                if self.cycle_count % 100 == 0:
                    self.cleanup_old_data()
                
                # Wait before next update
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping OHLC maintenance...")
                break
            except Exception as e:
                logger.error(f"Error in maintenance cycle: {e}")
                time.sleep(update_interval)

def main():
    """Main function"""
    print("=== QuestDB OHLC Maintenance ===")
    
    manager = OHLCManager()
    
    # Test connection
    result = manager.execute_query("SELECT count(*) FROM market_data;")
    if not result:
        print("❌ Cannot connect to QuestDB or market_data table not found")
        return
    
    tick_count = result['dataset'][0][0]
    print(f"✅ Connected to QuestDB - Found {tick_count} tick records")
    
    # Create tables
    print("\n🔧 Creating OHLC tables...")
    manager.create_ohlc_tables()
    
    # Initial update
    print("\n📊 Running initial OHLC update...")
    manager.update_all_timeframes()
    
    # Show stats
    manager.get_ohlc_stats()
    
    # Ask user if they want continuous mode
    response = input("\n🔄 Start continuous OHLC maintenance? (y/n): ").lower()
    if response == 'y':
        manager.run_continuous(update_interval=60)

if __name__ == "__main__":
    main()
