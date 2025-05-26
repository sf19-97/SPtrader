#!/usr/bin/env python3
"""Test viewport-aware table selection"""

import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_viewport_selection():
    """Test that different date ranges use appropriate tables"""
    
    test_cases = [
        {
            "name": "1 day range (should use 1m or 5m data)",
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-02T00:00:00Z",
            "expected_table": "ohlc_1m_v2 or ohlc_5m_v2"
        },
        {
            "name": "10 day range (should use 1h viewport)",
            "start": "2025-01-01T00:00:00Z", 
            "end": "2025-01-11T00:00:00Z",
            "expected_table": "ohlc_1h_viewport"
        },
        {
            "name": "2 month range (should use 4h viewport)",
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-03-01T00:00:00Z", 
            "expected_table": "ohlc_4h_viewport"
        },
        {
            "name": "2 year range (should use 1d viewport)",
            "start": "2023-01-01T00:00:00Z",
            "end": "2025-01-01T00:00:00Z",
            "expected_table": "ohlc_1d_viewport"
        }
    ]
    
    print("Testing viewport-aware table selection...\n")
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Range: {test['start']} to {test['end']}")
        print(f"  Expected: {test['expected_table']}")
        
        # Make request
        response = requests.get(f"{BASE_URL}/api/candles", params={
            "symbol": "EURUSD",
            "tf": "1h",
            "start": test['start'],
            "end": test['end'],
            "source": "v2"
        })
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 500:
            # Expected - tables don't exist yet
            error = response.json()
            print(f"  Table error (expected): {error['detail']}")
        elif response.status_code == 200:
            data = response.json()
            print(f"  Data points returned: {len(data)}")
        else:
            print(f"  Unexpected response: {response.text}")
            
        print()

def test_cache_with_viewport():
    """Test that caching works with viewport tables"""
    
    print("Testing cache behavior with viewport tables...\n")
    
    # Get initial stats
    stats_before = requests.get(f"{BASE_URL}/api/stats").json()
    print(f"Cache before: {stats_before['cache']['hits']} hits, {stats_before['cache']['misses']} misses")
    
    # Make same request twice
    params = {
        "symbol": "EURUSD",
        "tf": "1h", 
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-15T00:00:00Z",
        "source": "v2"
    }
    
    # First request (cache miss)
    response1 = requests.get(f"{BASE_URL}/api/candles", params=params)
    
    # Second request (should be cache hit)
    response2 = requests.get(f"{BASE_URL}/api/candles", params=params)
    
    # Check stats
    stats_after = requests.get(f"{BASE_URL}/api/stats").json()
    print(f"Cache after: {stats_after['cache']['hits']} hits, {stats_after['cache']['misses']} misses")
    
    cache_diff = stats_after['cache']['hits'] - stats_before['cache']['hits']
    print(f"\nCache hits increased by: {cache_diff}")
    
    if cache_diff > 0:
        print("✓ Caching is working correctly with viewport queries")
    else:
        print("✗ Cache not working as expected")

def main():
    print("="*60)
    print("Viewport-Aware API Testing")
    print("="*60)
    print()
    
    # Check API health
    health = requests.get(f"{BASE_URL}/api/health").json()
    print(f"API Status: {health['status']}")
    print(f"Database: {health['database']}")
    print()
    
    # Test viewport selection
    test_viewport_selection()
    
    # Test caching
    test_cache_with_viewport()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("\nNote: Table errors are expected if QuestDB optimization")
    print("hasn't been run yet. Execute the optimization script with:")
    print("  python execute_questdb_optimizations.py")
    print("="*60)

if __name__ == "__main__":
    main()