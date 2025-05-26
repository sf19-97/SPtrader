#!/usr/bin/env python3
"""Test current API functionality"""

import requests
import json

base_url = "http://localhost:8080/api/v1"

print("Testing SPtrader Go API...")
print("=" * 50)

# Test health endpoint
try:
    r = requests.get(f"{base_url}/health")
    print(f"✓ Health check: {r.status_code}")
    if r.status_code == 200:
        print(f"  Response: {r.json()}")
except Exception as e:
    print(f"✗ Health check failed: {e}")

# Test symbols endpoint
try:
    r = requests.get(f"{base_url}/symbols")
    print(f"\n✓ Symbols: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Available symbols: {', '.join(data['symbols'][:5])}...")
except Exception as e:
    print(f"\n✗ Symbols failed: {e}")

# Test candles endpoint
try:
    params = {
        "symbol": "EURUSD",
        "tf": "1h",
        "start": "2024-01-15T00:00:00Z",
        "end": "2024-01-15T12:00:00Z"
    }
    r = requests.get(f"{base_url}/candles", params=params)
    print(f"\n✓ Candles: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Retrieved {len(data['data'])} candles")
        if data['data']:
            print(f"  First candle: {data['data'][0]['time']} O:{data['data'][0]['open']}")
except Exception as e:
    print(f"\n✗ Candles failed: {e}")

# Test lazy loading endpoints (if available)
print("\n\nTesting lazy loading endpoints...")
print("-" * 30)

endpoints = [
    ("GET", "/data/check", {"symbol": "EURUSD", "start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"}),
    ("POST", "/data/ensure", {"symbol": "EURUSD", "start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"}),
    ("GET", "/candles/lazy", {"symbol": "EURUSD", "tf": "1h", "start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"})
]

for method, endpoint, data in endpoints:
    try:
        if method == "GET":
            r = requests.get(f"{base_url}{endpoint}", params=data)
        else:
            r = requests.post(f"{base_url}{endpoint}", json=data)
        
        if r.status_code == 404:
            print(f"✗ {endpoint}: Not implemented yet")
        else:
            print(f"✓ {endpoint}: {r.status_code}")
    except Exception as e:
        print(f"✗ {endpoint}: {e}")

print("\n" + "=" * 50)
print("Note: Lazy loading endpoints need API rebuild to be available")