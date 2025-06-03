#!/usr/bin/env python3
"""
Test the virtual scrolling implementation
"""
import time
import subprocess
import requests

def test_virtual_scrolling():
    print("🧪 Testing Virtual Scrolling Implementation")
    print("=" * 60)
    
    # Check if services are running
    try:
        response = requests.get("http://localhost:8080/api/v1/health")
        print("✅ API is running")
    except:
        print("❌ API is not running. Starting services...")
        subprocess.run(["./start_locked.sh"], cwd="/home/millet_frazier/SPtrader")
        time.sleep(5)
    
    # Test data range endpoint
    print("\n📊 Testing data range endpoint:")
    response = requests.get("http://localhost:8080/api/v1/data/range?symbol=EURUSD")
    if response.ok:
        data = response.json()
        print(f"  Available data: {data['start']} to {data['end']}")
    
    # Test native candles endpoint
    print("\n🕯️ Testing native candles endpoint:")
    params = {
        "symbol": "EURUSD",
        "tf": "1h",
        "start": "2024-01-10T00:00:00Z",
        "end": "2024-01-10T12:00:00Z"
    }
    response = requests.get("http://localhost:8080/api/v1/candles/native/v2", params=params)
    if response.ok:
        data = response.json()
        print(f"  Received {data['count']} candles")
        print(f"  Method: {data['method']}")
    
    print("\n✨ Virtual Scrolling Features:")
    print("  1. Only keeps 2000 candles in memory")
    print("  2. Dynamically loads data as you scroll")
    print("  3. Intelligent caching system")
    print("  4. Resolution selector (not activated yet)")
    
    print("\n📱 To test in the UI:")
    print("  1. Open the desktop app")
    print("  2. Watch the status bar - it should show 'Virtual Scrolling Active'")
    print("  3. Scroll around - data loads dynamically")
    print("  4. Check console for loading messages")
    
    print("\n🚀 Next Steps (from the plan):")
    print("  - Phase 2: Smart Resolution Switching (ready but not activated)")
    print("  - Phase 3: Predictive Loading")
    print("  - Phase 4: WebSocket Streaming")

if __name__ == "__main__":
    test_virtual_scrolling()