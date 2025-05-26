#!/usr/bin/env python3
"""Test script for the FastAPI backend"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data
    print("✓ Health check passed")
    return data

def test_timeframes():
    """Test timeframes endpoint"""
    response = requests.get(f"{BASE_URL}/api/timeframes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "1m" in data
    assert "1h" in data
    print(f"✓ Timeframes endpoint passed, found {len(data)} timeframes")
    return data

def test_stats():
    """Test stats endpoint"""
    response = requests.get(f"{BASE_URL}/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cache" in data
    assert "database" in data
    print("✓ Stats endpoint passed")
    return data

def test_candles_validation():
    """Test candles endpoint validation"""
    # Test missing parameters
    response = requests.get(f"{BASE_URL}/api/candles")
    assert response.status_code == 422
    print("✓ Missing parameters validation passed")
    
    # Test invalid timeframe
    response = requests.get(f"{BASE_URL}/api/candles", params={
        "symbol": "EURUSD",
        "tf": "invalid",
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-02T00:00:00Z"
    })
    assert response.status_code == 422
    print("✓ Invalid timeframe validation passed")
    
    # Test invalid date range
    response = requests.get(f"{BASE_URL}/api/candles", params={
        "symbol": "EURUSD",
        "tf": "1h",
        "start": "2025-01-02T00:00:00Z",
        "end": "2025-01-01T00:00:00Z"
    })
    assert response.status_code == 400
    data = response.json()
    assert "Start time must be before end time" in data["detail"]
    print("✓ Invalid date range validation passed")
    
    # Test range too large
    response = requests.get(f"{BASE_URL}/api/candles", params={
        "symbol": "EURUSD",
        "tf": "1m",
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-10T00:00:00Z"
    })
    assert response.status_code == 400
    data = response.json()
    assert "Range too large" in data["detail"]
    print("✓ Range too large validation passed")

def test_cors():
    """Test CORS headers"""
    response = requests.options(f"{BASE_URL}/api/health", headers={
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    print("✓ CORS headers passed")

def main():
    """Run all tests"""
    print("Testing FastAPI Backend...\n")
    
    # Test endpoints
    health = test_health()
    print(f"  Database status: {health['database']}")
    
    timeframes = test_timeframes()
    print(f"  Available timeframes: {', '.join(timeframes)}")
    
    stats = test_stats()
    print(f"  Cache size: {stats['cache']['size']}/{stats['cache']['max_size']}")
    print(f"  Database pool: {stats['database']['pool_free']}/{stats['database']['pool_size']} free")
    
    # Test validation
    print("\nTesting validation...")
    test_candles_validation()
    
    # Test CORS
    print("\nTesting CORS...")
    test_cors()
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()