#!/usr/bin/env python3
"""
Verify that all timeframes now show consistent data using the quality system
Created: May 30, 2025
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8080/api/v1"

def main():
    # Get quality recommendations
    quality_resp = requests.get(f"{API_BASE}/data/quality/v2?symbol=EURUSD")
    quality = quality_resp.json()
    
    print("Data Quality System Status")
    print("=========================")
    print(f"Latest Good Day: {quality['latest_good_day']['date']}")
    print(f"Quality: {quality['latest_good_day']['quality_rating']} (Score: {quality['latest_good_day']['quality_score']})")
    print(f"\nQuality Distribution: {json.dumps(quality['quality_distribution'], indent=2)}")
    
    print("\n\nTimeframe Consistency Check")
    print("===========================")
    
    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    for tf in timeframes:
        if tf in quality['suggested_ranges']:
            range_info = quality['suggested_ranges'][tf]
            
            # Fetch candle count for this range
            candles_resp = requests.get(
                f"{API_BASE}/candles/native/v2",
                params={
                    'symbol': 'EURUSD',
                    'tf': tf,
                    'start': range_info['start'],
                    'end': range_info['end']
                }
            )
            
            if candles_resp.status_code == 200:
                candles_data = candles_resp.json()
                
                # Handle both array and object response formats
                if isinstance(candles_data, dict) and 'candles' in candles_data:
                    candles = candles_data['candles']
                elif isinstance(candles_data, dict) and 'data' in candles_data:
                    candles = candles_data['data']
                elif isinstance(candles_data, list):
                    candles = candles_data
                else:
                    candles = []
                
                candle_count = len(candles)
                
                # Get first and last candle times
                if candles:
                    # Handle both 'time' and 'timestamp' fields
                    time_field = 'timestamp' if 'timestamp' in candles[0] else 'time'
                    first_time = datetime.fromisoformat(candles[0][time_field].replace('Z', '+00:00'))
                    last_time = datetime.fromisoformat(candles[-1][time_field].replace('Z', '+00:00'))
                    
                    print(f"\n{tf:>3}: {candle_count:>5} candles")
                    print(f"      Range: {range_info['start'][:10]} to {range_info['end'][:10]}")
                    print(f"      Good days: {range_info['good_days']} out of {range_info['total_days']}")
                    print(f"      First: {first_time.strftime('%Y-%m-%d %H:%M')}")
                    print(f"      Last:  {last_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"\n{tf:>3}: No candles returned")
            else:
                print(f"\n{tf:>3}: Error fetching candles: {candles_resp.status_code}")

if __name__ == "__main__":
    main()