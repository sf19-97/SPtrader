#!/usr/bin/env python3
"""
Oanda Live Forex Data Feed to QuestDB
Streams live forex prices from Oanda API directly into QuestDB market_data table
"""

import os
import requests
import json
import time
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OandaQuestDBFeeder:
    def __init__(self):
        # Hardcoded for testing - REMOVE BEFORE SHARING CODE!
        self.api_token = "839953525bd59fb3b79ea8513a8b0e93-a0181385f4286c8bc91dbdfacea7b43c"
        self.account_id = "001-001-9439158-001"
        
        # Oanda API configuration
        self.oanda_base_url = "https://api-fxtrade.oanda.com"  # Live environment
        # For demo: self.oanda_base_url = "https://api-fxpractice.oanda.com"
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # QuestDB configuration
        self.questdb_url = "http://localhost:9000"
        
        # Currency pairs to track
        self.instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]
    
    def determine_trading_session(self, utc_hour):
        """
        Determine forex trading session based on UTC hour
        
        Sessions:
        - Sydney: 21:00-06:00 UTC (Sunday-Thursday)
        - Tokyo: 00:00-09:00 UTC (Monday-Friday)
        - London: 08:00-17:00 UTC (Monday-Friday)
        - New York: 13:00-22:00 UTC (Monday-Friday)
        
        Overlaps:
        - Sydney+Tokyo: 00:00-06:00 UTC
        - Tokyo+London: 08:00-09:00 UTC
        - London+New York: 13:00-17:00 UTC
        """
        # Check for overlaps first (higher priority)
        if 0 <= utc_hour < 6:
            return "SYDNEY_TOKYO"
        elif utc_hour == 8:
            return "TOKYO_LONDON"
        elif 13 <= utc_hour < 17:
            return "LONDON_NEW_YORK"
        
        # Individual sessions
        elif 21 <= utc_hour or utc_hour < 6:
            return "SYDNEY"
        elif 0 <= utc_hour < 9:
            return "TOKYO"
        elif 8 <= utc_hour < 17:
            return "LONDON"
        elif 13 <= utc_hour < 22:
            return "NEW_YORK"
        else:
            return "CLOSED"
    
    def is_market_open(self, utc_hour, day_of_week):
        """
        Determine if forex markets are open
        
        Forex Trading Hours:
        - Opens: Sunday 22:00 UTC
        - Closes: Friday 22:00 UTC
        - Closed: Friday 22:00 UTC → Sunday 22:00 UTC (48 hours)
        """
        if day_of_week == 5:  # Friday
            return utc_hour < 22  # Open until 22:00 UTC, then closed
        elif day_of_week == 6:  # Saturday
            return False  # Closed all day
        elif day_of_week == 7:  # Sunday
            return utc_hour >= 22  # Closed until 22:00 UTC, then open
        else:  # Monday-Thursday
            return True  # Open 24 hours
    
    def get_live_prices(self):
        """Get current live prices from Oanda"""
        try:
            instruments_str = ",".join(self.instruments)
            url = f"{self.oanda_base_url}/v3/accounts/{self.account_id}/pricing"
            params = {"instruments": instruments_str}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Oanda API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return None
    
    def process_price_data(self, oanda_response):
        """Convert Oanda price data to our market_data format"""
        if not oanda_response or 'prices' not in oanda_response:
            return []
        
        processed_data = []
        now = datetime.now(timezone.utc)
        
        for price_info in oanda_response['prices']:
            try:
                instrument = price_info['instrument']
                symbol = instrument.replace('_', '')  # EUR_USD -> EURUSD
                
                # Get bid/ask prices
                bid = float(price_info['bids'][0]['price'])
                ask = float(price_info['asks'][0]['price'])
                mid_price = (bid + ask) / 2
                spread = ask - bid
                
                # Calculate timing data
                hour_of_day = now.hour
                day_of_week = now.isoweekday()  # Monday=1, Sunday=7
                trading_session = self.determine_trading_session(hour_of_day)
                market_open = self.is_market_open(hour_of_day, day_of_week)
                
                # Volume (Oanda doesn't provide volume in pricing, so we'll use 0)
                volume = 0.0
                
                data_point = {
                    'timestamp': now.isoformat().replace('+00:00', 'Z'),
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'price': mid_price,
                    'spread': spread,
                    'hour_of_day': hour_of_day,
                    'day_of_week': day_of_week,
                    'trading_session': trading_session,
                    'volume': volume,
                    'market_open': market_open
                }
                
                processed_data.append(data_point)
                
            except Exception as e:
                logger.error(f"Error processing {price_info.get('instrument', 'unknown')}: {e}")
                continue
        
        return processed_data
    
    def insert_to_questdb(self, data_points):
        """Insert data into QuestDB market_data table"""
        if not data_points:
            return False
        
        try:
            # Build INSERT statement
            values = []
            for data in data_points:
                values.append(
                    f"('{data['timestamp']}', '{data['symbol']}', "
                    f"{data['bid']}, {data['ask']}, {data['price']}, {data['spread']}, "
                    f"{data['hour_of_day']}, {data['day_of_week']}, '{data['trading_session']}', "
                    f"{data['volume']}, {data['market_open']}, 'oanda')"
                )
            
            query = f"""
            INSERT INTO market_data 
            (timestamp, symbol, bid, ask, price, spread, hour_of_day, day_of_week, trading_session, volume, market_open, data_source)
            VALUES {', '.join(values)};
            """
            
            response = requests.get(f"{self.questdb_url}/exec", params={"query": query})
            
            if response.status_code == 200:
                logger.info(f"Successfully inserted {len(data_points)} price records")
                return True
            else:
                logger.error(f"QuestDB insert failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error inserting to QuestDB: {e}")
            return False
    
    def run_once(self):
        """Run one cycle of data collection"""
        logger.info("Fetching live prices from Oanda...")
        
        # Get live prices
        oanda_data = self.get_live_prices()
        if not oanda_data:
            logger.warning("No data received from Oanda")
            return False
        
        # Process the data
        processed_data = self.process_price_data(oanda_data)
        if not processed_data:
            logger.warning("No valid price data to process")
            return False
        
        # Insert into QuestDB
        success = self.insert_to_questdb(processed_data)
        
        if success:
            for data in processed_data:
                logger.info(f"{data['symbol']}: {data['price']:.5f} (session: {data['trading_session']})")
        
        return success
    
    def run_continuous(self, interval_seconds=10):
        """Run continuous data collection"""
        logger.info(f"Starting continuous Oanda data feed (every {interval_seconds}s)")
        logger.info(f"Tracking instruments: {', '.join(self.instruments)}")
        
        while True:
            try:
                self.run_once()
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Stopping data feed...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(interval_seconds)

def main():
    """Main function"""
    print("=== Oanda to QuestDB Live Feed ===")
    
    # Check if credentials are hardcoded (they are now!)
    print("\n✅ Credentials hardcoded for testing")
    
    try:
        feeder = OandaQuestDBFeeder()
        
        # Test single run first
        print("\n🧪 Testing single data fetch...")
        success = feeder.run_once()
        
        if success:
            print("\n✅ Test successful! Data inserted into QuestDB.")
            
            # Auto-start continuous mode when running as background process
            import sys
            if not sys.stdin.isatty():  # Running in background
                print("🔄 Auto-starting continuous feed...")
                feeder.run_continuous(interval_seconds=10)
            else:
                # Ask user if they want continuous mode
                response = input("\n🔄 Start continuous feed? (y/n): ").lower()
                if response == 'y':
                    feeder.run_continuous(interval_seconds=10)
        else:
            print("\n❌ Test failed. Check your credentials and QuestDB connection.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
