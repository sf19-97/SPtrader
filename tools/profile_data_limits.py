#!/usr/bin/env python3
"""
Profile data limits to establish performance boundaries
This will inform our frontend design
"""

import asyncio
import asyncpg
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class DataProfiler:
    def __init__(self, db_url="postgresql://admin:quest@localhost:8812/qdb"):
        self.db_url = db_url
        self.results = {}
        
    async def profile_all_tables(self):
        """Profile all viewport tables to find performance limits"""
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Tables to profile with typical query ranges
            tables = [
                ("market_data_v2", "tick", timedelta(minutes=5)),
                ("ohlc_1m_v2", "1m", timedelta(hours=4)),
                ("ohlc_5m_v2", "5m", timedelta(days=1)),
                ("ohlc_15m_v2", "15m", timedelta(days=7)),
                ("ohlc_1h_v2", "1h", timedelta(days=30)),
                ("ohlc_4h_viewport", "4h", timedelta(days=90)),
                ("ohlc_1d_viewport", "1d", timedelta(days=365)),
            ]
            
            print("🔍 Profiling Data Tables")
            print("=" * 80)
            
            for table_name, resolution, time_range in tables:
                result = await self.profile_table(conn, table_name, resolution, time_range)
                self.results[resolution] = result
                
                print(f"\n📊 {table_name} ({resolution}):")
                print(f"   Points returned: {result['points']}")
                print(f"   Query time: {result['query_ms']:.1f}ms")
                print(f"   Points/ms: {result['points_per_ms']:.2f}")
                print(f"   Status: {result['status']}")
                
        finally:
            await conn.close()
    
    async def profile_table(self, conn, table: str, resolution: str, time_range: timedelta) -> Dict:
        """Profile a single table with given parameters"""
        end_time = datetime.utcnow()
        start_time = end_time - time_range
        
        # Build query
        query = f"""
            SELECT 
                timestamp,
                open,
                high,
                low,
                close,
                volume
            FROM {table}
            WHERE symbol = 'EURUSD'
            AND timestamp >= $1
            AND timestamp <= $2
            ORDER BY timestamp
        """
        
        # Time the query
        start = time.time()
        try:
            rows = await conn.fetch(query, start_time, end_time)
            query_time = (time.time() - start) * 1000  # ms
            
            points = len(rows)
            
            # Determine performance status
            if query_time < 50:
                status = "⚡ Excellent"
            elif query_time < 100:
                status = "✅ Good"
            elif query_time < 500:
                status = "🔶 Acceptable"
            else:
                status = "🐌 Slow"
            
            return {
                "table": table,
                "resolution": resolution,
                "time_range_hours": int(time_range.total_seconds() / 3600),
                "points": points,
                "query_ms": query_time,
                "points_per_ms": points / query_time if query_time > 0 else 0,
                "status": status,
                "memory_estimate_mb": (points * 48) / 1024 / 1024  # ~48 bytes per candle
            }
            
        except Exception as e:
            return {
                "table": table,
                "resolution": resolution,
                "error": str(e),
                "status": "❌ Failed"
            }
    
    async def find_optimal_ranges(self):
        """Based on profiling, determine optimal query ranges"""
        conn = await asyncpg.connect(self.db_url)
        
        print("\n\n🎯 Finding Optimal Query Ranges")
        print("=" * 80)
        
        resolutions = [
            ("ohlc_5m_v2", "5m", [1, 4, 12, 24, 48, 168]),  # hours
            ("ohlc_1h_v2", "1h", [24, 168, 720, 2160]),     # hours
            ("ohlc_4h_viewport", "4h", [168, 720, 2160, 4320]),  # hours
            ("ohlc_1d_viewport", "1d", [720, 2160, 8760, 17520]),  # hours
        ]
        
        optimal = {}
        
        try:
            for table, resolution, hour_ranges in resolutions:
                print(f"\n Testing {resolution} resolution:")
                
                for hours in hour_ranges:
                    result = await self.profile_table(
                        conn, table, resolution, timedelta(hours=hours)
                    )
                    
                    print(f"   {hours:5d} hours: {result['points']:5d} points, "
                          f"{result['query_ms']:6.1f}ms {result['status']}")
                    
                    # Find the sweet spot (< 100ms)
                    if resolution not in optimal and result['query_ms'] < 100:
                        optimal[resolution] = {
                            "max_hours": hours,
                            "max_points": result['points'],
                            "typical_ms": result['query_ms']
                        }
        finally:
            await conn.close()
        
        return optimal
    
    def generate_data_contract(self):
        """Generate a data contract based on profiling"""
        optimal = asyncio.run(self.find_optimal_ranges())
        
        contract = {
            "max_points_per_request": 500,  # Conservative limit
            "resolution_limits": {},
            "performance_targets": {
                "excellent": 50,   # ms
                "good": 100,      # ms
                "acceptable": 500  # ms
            }
        }
        
        # Build resolution-specific limits
        for resolution, data in optimal.items():
            contract["resolution_limits"][resolution] = {
                "max_time_range_hours": data["max_hours"],
                "max_points": min(data["max_points"], 500),
                "typical_query_ms": data["typical_ms"],
                "recommended_for": self.get_recommendation(resolution, data["max_hours"])
            }
        
        return contract
    
    def get_recommendation(self, resolution: str, max_hours: int) -> str:
        """Get usage recommendation for resolution"""
        if resolution == "5m":
            return "Intraday detail view"
        elif resolution == "1h":
            return "Daily to weekly analysis"
        elif resolution == "4h":
            return "Weekly to monthly trends"
        elif resolution == "1d":
            return "Long-term analysis"
        return "General use"
    
    def save_contract(self, contract: Dict):
        """Save the data contract for frontend use"""
        with open("data_contract.json", "w") as f:
            json.dump(contract, f, indent=2)
        
        print("\n\n📄 Data Contract Generated")
        print("=" * 80)
        print(json.dumps(contract, indent=2))
        
        # Also generate TypeScript interface
        ts_interface = self.generate_typescript_interface(contract)
        with open("data_contract.ts", "w") as f:
            f.write(ts_interface)
        
        print("\n\n📘 TypeScript Interface Generated")
        print("=" * 80)
        print(ts_interface)
    
    def generate_typescript_interface(self, contract: Dict) -> str:
        """Generate TypeScript interface from contract"""
        ts = """// Auto-generated from data profiling
export interface DataContract {
    maxPointsPerRequest: number;
    resolutionLimits: {
        [resolution: string]: {
            maxTimeRangeHours: number;
            maxPoints: number;
            typicalQueryMs: number;
            recommendedFor: string;
        };
    };
    performanceTargets: {
        excellent: number;
        good: number;
        acceptable: number;
    };
}

export const DATA_CONTRACT: DataContract = """
        
        # Convert Python dict to JS object
        import json
        ts += json.dumps(contract, indent=2).replace('_', '')
        ts += ";\n"
        
        return ts

async def main():
    profiler = DataProfiler()
    
    # First, profile all tables
    await profiler.profile_all_tables()
    
    # Generate and save contract
    contract = profiler.generate_data_contract()
    profiler.save_contract(contract)
    
    print("\n\n✅ Profiling Complete!")
    print("Use data_contract.json and data_contract.ts to build your frontend")

if __name__ == "__main__":
    asyncio.run(main())