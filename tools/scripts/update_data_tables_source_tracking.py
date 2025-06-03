#!/usr/bin/env python3
"""
Update SPtrader data tables to track data source (Dukascopy vs Oanda)
This helps maintain data quality awareness and enables smart data replacement
"""

import requests
import time
import sys
from datetime import datetime

class DataTableUpdater:
    def __init__(self, questdb_url="http://localhost:9000"):
        self.questdb_url = questdb_url
        self.updates_applied = []
        self.errors = []
        
    def execute_query(self, query: str, description: str = "") -> bool:
        """Execute a single query with error handling"""
        try:
            print(f"  → {description}...", end='', flush=True)
            response = requests.get(
                f"{self.questdb_url}/exec",
                params={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                print(" ✅")
                self.updates_applied.append(description)
                return True
            else:
                print(f" ❌ ({response.status_code})")
                self.errors.append(f"{description}: {response.text}")
                return False
                
        except Exception as e:
            print(f" ❌ ({str(e)})")
            self.errors.append(f"{description}: {str(e)}")
            return False
    
    def check_column_exists(self, table: str, column: str) -> bool:
        """Check if column already exists in table"""
        try:
            response = requests.get(
                f"{self.questdb_url}/exec",
                params={"query": f"SELECT {column} FROM {table} LIMIT 1"},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def update_data_tables(self):
        """Add data_source column to all relevant tables"""
        print("\n🔄 Updating Data Tables for Source Tracking")
        print("=" * 50)
        
        # Tables to update
        tables_to_update = [
            ('market_data', 'Original Oanda tick data'),
            ('market_data_v2', 'Dukascopy tick data'),
        ]
        
        # Check each table
        for table, description in tables_to_update:
            print(f"\n📊 Checking {table} ({description})...")
            
            # Check if table exists
            if not self.table_exists(table):
                print(f"  ⚠️  Table {table} does not exist, skipping")
                continue
            
            # Check if column already exists
            if self.check_column_exists(table, 'data_source'):
                print(f"  ℹ️  Column 'data_source' already exists in {table}")
                continue
            
            # Add column
            if table == 'market_data':
                # Original table gets 'oanda' as default
                query = f"ALTER TABLE {table} ADD COLUMN data_source SYMBOL"
                self.execute_query(query, f"Add data_source column to {table}")
                
                # Update existing records
                query2 = f"UPDATE {table} SET data_source = 'oanda' WHERE data_source IS NULL"
                self.execute_query(query2, f"Set existing {table} records to 'oanda'")
                
            elif table == 'market_data_v2':
                # V2 table gets 'dukascopy' as default
                query = f"ALTER TABLE {table} ADD COLUMN data_source SYMBOL"
                self.execute_query(query, f"Add data_source column to {table}")
                
                # Update existing records
                query2 = f"UPDATE {table} SET data_source = 'dukascopy' WHERE data_source IS NULL"
                self.execute_query(query2, f"Set existing {table} records to 'dukascopy'")
        
        # Also update OHLC tables
        print("\n📊 Updating OHLC tables...")
        timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
        for tf in timeframes:
            for suffix in ['', '_v2']:
                table = f'ohlc_{tf}{suffix}'
                
                if not self.table_exists(table):
                    continue
                
                if self.check_column_exists(table, 'data_source'):
                    print(f"  ℹ️  Column already exists in {table}")
                    continue
                
                query = f"ALTER TABLE {table} ADD COLUMN data_source SYMBOL"
                self.execute_query(query, f"Add data_source to {table}")
                
                # Set default based on table type
                default_source = 'dukascopy' if '_v2' in table else 'oanda'
                query2 = f"UPDATE {table} SET data_source = '{default_source}' WHERE data_source IS NULL"
                self.execute_query(query2, f"Set {table} source to '{default_source}'")
    
    def table_exists(self, table: str) -> bool:
        """Check if table exists"""
        try:
            response = requests.get(
                f"{self.questdb_url}/exec",
                params={"query": f"SELECT count(*) FROM {table} LIMIT 1"},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def update_oanda_feed_script(self):
        """Show how to update the Oanda feed script"""
        print("\n📝 Update Instructions for oanda_feed.py:")
        print("=" * 50)
        print("""
In ~/SPtrader/data_feeds/oanda_feed.py, modify the insert_to_questdb method:

1. Find the INSERT statement (around line 140-150)
2. Update it to include data_source:

OLD:
    INSERT INTO market_data 
    (timestamp, symbol, bid, ask, price, spread, hour_of_day, day_of_week, trading_session, volume, market_open)
    VALUES ...

NEW:
    INSERT INTO market_data 
    (timestamp, symbol, bid, ask, price, spread, hour_of_day, day_of_week, trading_session, volume, market_open, data_source)
    VALUES ...

3. Update the values to include 'oanda':

OLD:
    f"({data['timestamp']}, '{data['symbol']}', ... {data['market_open']})"

NEW:
    f"({data['timestamp']}, '{data['symbol']}', ... {data['market_open']}, 'oanda')"
""")
    
    def show_summary(self):
        """Show summary of updates"""
        print("\n" + "=" * 50)
        print("📊 Update Summary")
        print("=" * 50)
        
        if self.updates_applied:
            print(f"\n✅ Successful Updates ({len(self.updates_applied)}):")
            for update in self.updates_applied:
                print(f"  • {update}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        print("\n🔍 Verify the updates:")
        print("  sptrader db query \"SELECT DISTINCT data_source FROM market_data LIMIT 5\"")
        print("  sptrader db query \"SELECT DISTINCT data_source FROM market_data_v2 LIMIT 5\"")


def main():
    print("""
╔═══════════════════════════════════════════════════╗
║     SPtrader Data Table Update Utility v1.0       ║
║         Add Source Tracking to Your Data          ║
╚═══════════════════════════════════════════════════╝
    """)
    
    # Check if QuestDB is running
    try:
        response = requests.get("http://localhost:9000/exec?query=SELECT%201", timeout=5)
        if response.status_code != 200:
            print("❌ QuestDB is not responding properly")
            sys.exit(1)
    except:
        print("❌ Cannot connect to QuestDB. Is it running?")
        print("   Run: sptrader start")
        sys.exit(1)
    
    print("✅ Connected to QuestDB\n")
    
    # Confirm with user
    print("This script will:")
    print("  1. Add 'data_source' column to all data tables")
    print("  2. Mark existing data with appropriate source")
    print("  3. Show you how to update oanda_feed.py")
    print("")
    
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Run updates
    updater = DataTableUpdater()
    updater.update_data_tables()
    updater.update_oanda_feed_script()
    updater.show_summary()
    
    print("\n✅ Done! Your tables now track data sources.")
    print("\n💡 Next steps:")
    print("  1. Update oanda_feed.py as shown above")
    print("  2. Restart the Oanda feed: sptrader restart")
    print("  3. New data will be tagged with its source")


if __name__ == "__main__":
    main()
