#!/usr/bin/env python3
"""
Verify that all timeframes are working correctly
"""
import requests
import json

API_BASE = "http://localhost:8080/api/v1"

def test_timeframe(symbol="EURUSD", start="2024-01-10T12:00:00Z", end="2024-01-10T13:00:00Z"):
    """Test all timeframes for the same hour of data"""
    
    timeframes = ["1m", "5m", "15m", "30m", "1h"]
    results = {}
    
    print(f"🔍 Testing candle generation for {symbol}")
    print(f"📅 Period: {start} to {end}")
    print("=" * 60)
    
    for tf in timeframes:
        url = f"{API_BASE}/candles/native/v2"
        params = {
            "symbol": symbol,
            "tf": tf,
            "start": start,
            "end": end
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "candles" in data:
            candles = data["candles"]
            total_ticks = sum(c.get("tick_count", 0) for c in candles)
            
            results[tf] = {
                "candle_count": len(candles),
                "total_ticks": total_ticks,
                "first_open": candles[0]["open"] if candles else None,
                "last_close": candles[-1]["close"] if candles else None
            }
            
            print(f"\n{tf:>3}: {len(candles):>3} candles, {total_ticks:>5} total ticks")
            if candles:
                print(f"     Open: {candles[0]['open']:.5f}, Close: {candles[-1]['close']:.5f}")
    
    # Verify consistency
    print("\n" + "="*60)
    print("✅ Consistency Check:")
    
    tick_counts = [r["total_ticks"] for r in results.values() if r["total_ticks"] > 0]
    if len(set(tick_counts)) == 1:
        print(f"✓ All timeframes use the same {tick_counts[0]} ticks")
    else:
        print(f"✗ Tick count mismatch: {tick_counts}")
    
    # Check price consistency
    opens = [r["first_open"] for r in results.values() if r["first_open"]]
    closes = [r["last_close"] for r in results.values() if r["last_close"]]
    
    if len(set(opens)) == 1:
        print(f"✓ All timeframes start at {opens[0]:.5f}")
    else:
        print(f"✗ Opening price mismatch: {set(opens)}")
        
    if len(set(closes)) == 1:
        print(f"✓ All timeframes end at {closes[0]:.5f}")
    else:
        print(f"✗ Closing price mismatch: {set(closes)}")

if __name__ == "__main__":
    test_timeframe()