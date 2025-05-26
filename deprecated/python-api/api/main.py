from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncpg
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
import time
import logging
from contextlib import asynccontextmanager
import gzip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
db_pool = None
cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}

# Configuration
DB_HOST = "localhost"
DB_PORT = 8812
DB_USER = "admin"
DB_PASSWORD = "quest"
DB_NAME = "qdb"
MAX_CANDLES_PER_REQUEST = 10000
CACHE_SIZE = 128  # Number of cached responses

# Supported timeframes
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

# Cache configuration
HISTORICAL_CACHE_TTL = 300  # 5 minutes for historical data
RECENT_CACHE_TTL = 10  # 10 seconds for recent data


class CachedResponse:
    def __init__(self, data: List[Dict], timestamp: float):
        self.data = data
        self.timestamp = timestamp
        
    def is_expired(self, ttl: float) -> bool:
        return time.time() - self.timestamp > ttl


# Simple cache dictionary (since lru_cache doesn't work well with our use case)
candle_cache: Dict[str, CachedResponse] = {}


def get_cached_candles(cache_key: str) -> Optional[CachedResponse]:
    return candle_cache.get(cache_key)


def set_cached_candles(cache_key: str, data: List[Dict]):
    global candle_cache
    
    # Remove oldest entries if cache is full
    if len(candle_cache) >= CACHE_SIZE:
        # Remove 10% of oldest entries
        items_to_remove = max(1, CACHE_SIZE // 10)
        sorted_keys = sorted(candle_cache.keys(), 
                           key=lambda k: candle_cache[k].timestamp)
        for key in sorted_keys[:items_to_remove]:
            del candle_cache[key]
    
    # Add new entry
    candle_cache[cache_key] = CachedResponse(data, time.time())


def generate_cache_key(symbol: str, tf: str, start: str, end: str, source: str) -> str:
    key_string = f"{symbol}:{tf}:{start}:{end}:{source}"
    return hashlib.md5(key_string.encode()).hexdigest()


async def init_db_pool():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        logger.warning("Running in development mode without database connection")


async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db_pool()
    yield
    # Shutdown
    await close_db_pool()


# Create FastAPI app
app = FastAPI(title="SPTrader API", version="1.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_candle_data(rows: List[asyncpg.Record], timeframe: str) -> List[Dict]:
    """Format database rows into frontend-compatible candle format"""
    candles = []
    for row in rows:
        candle = {
            "time": int(row['timestamp'].timestamp()),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "volume": float(row.get('volume', 0))
        }
        candles.append(candle)
    return candles


def get_table_name(symbol: str, timeframe: str, source: str) -> str:
    """Generate table name based on symbol, timeframe and source"""
    if source == "v1":
        return f"{symbol.lower()}_{timeframe}_oanda"
    else:  # v2
        return f"{symbol.lower()}_{timeframe}"


def get_data_quality_preference() -> str:
    """
    Determine which data source to prefer based on availability.
    Returns 'dukascopy' if available, otherwise 'oanda'
    """
    # This could be made more sophisticated to check actual data availability
    # For now, prefer Dukascopy (v2) when available
    return "v2"


def get_viewport_table(symbol: str, start_dt: datetime, end_dt: datetime, source: str) -> str:
    """Select the best table based on viewport duration"""
    duration = end_dt - start_dt
    
    # For v2 data (multi-symbol tables)
    if source == "v2":
        if duration.days > 365:
            return "ohlc_1d_viewport"
        elif duration.days > 30:
            return "ohlc_4h_viewport"
        elif duration.days > 7:
            return "ohlc_1h_viewport"
        else:
            # Use original tables for fine-grained data
            if duration.total_seconds() <= 86400:  # <= 1 day
                return "ohlc_1m_v2"
            else:
                return "ohlc_5m_v2"
    
    # For v1 data (Oanda, single symbol tables)
    else:
        symbol_lower = symbol.lower()
        if duration.days > 365:
            return f"{symbol_lower}_1d_viewport_oanda"
        elif duration.days > 30:
            return f"{symbol_lower}_4h_viewport_oanda"
        elif duration.days > 7:
            return f"{symbol_lower}_1h_viewport_oanda"
        else:
            # Use original tables for fine-grained data
            if duration.total_seconds() <= 86400:  # <= 1 day
                return f"{symbol_lower}_1m_oanda"
            else:
                return f"{symbol_lower}_5m_oanda"


@app.get("/api/candles")
async def get_candles(
    symbol: str = Query(..., description="Currency pair (e.g., EURUSD)"),
    tf: str = Query(..., description="Timeframe", pattern=f"^({'|'.join(TIMEFRAMES)})$"),
    start: str = Query(..., description="ISO timestamp for range start"),
    end: str = Query(..., description="ISO timestamp for range end"),
    source: str = Query("v2", description="Data source version", pattern="^(v1|v2)$")
) -> List[Dict]:
    global cache_stats
    cache_stats["total_requests"] += 1
    
    # Validate timestamps
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start time must be before end time")
    
    # Check if range is too large
    time_diff = end_dt - start_dt
    if tf == "1m" and time_diff > timedelta(days=7):
        raise HTTPException(status_code=400, detail="Range too large for 1m timeframe (max 7 days)")
    elif tf in ["5m", "15m"] and time_diff > timedelta(days=30):
        raise HTTPException(status_code=400, detail="Range too large for this timeframe (max 30 days)")
    
    # Generate cache key
    cache_key = generate_cache_key(symbol, tf, start, end, source)
    
    # Check cache
    cached_response = get_cached_candles(cache_key)
    if cached_response:
        # Determine TTL based on data recency
        is_recent = end_dt > datetime.now() - timedelta(hours=1)
        ttl = RECENT_CACHE_TTL if is_recent else HISTORICAL_CACHE_TTL
        
        if not cached_response.is_expired(ttl):
            cache_stats["hits"] += 1
            return cached_response.data
    
    cache_stats["misses"] += 1
    
    # Query database
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    # Use viewport-aware table selection
    table_name = get_viewport_table(symbol, start_dt, end_dt, source)
    
    # Build query based on table type
    if source == "v2" and "viewport" in table_name:
        # Multi-symbol viewport tables need symbol filter
        query = f"""
            SELECT timestamp, open, high, low, close, volume
            FROM {table_name}
            WHERE symbol = $1 AND timestamp >= $2 AND timestamp < $3
            ORDER BY timestamp ASC
            LIMIT {MAX_CANDLES_PER_REQUEST}
        """
        query_params = [symbol, start_dt, end_dt]
    else:
        # Single-symbol tables don't need symbol filter
        query = f"""
            SELECT timestamp, open, high, low, close, volume
            FROM {table_name}
            WHERE timestamp >= $1 AND timestamp < $2
            ORDER BY timestamp ASC
            LIMIT {MAX_CANDLES_PER_REQUEST}
        """
        query_params = [start_dt, end_dt]
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *query_params)
            
        if not rows:
            return []
        
        # Format data
        candles = format_candle_data(rows, tf)
        
        # Cache the result
        set_cached_candles(cache_key, candles)
        
        return candles
        
    except asyncpg.UndefinedTableError:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/api/symbols")
async def get_symbols() -> List[str]:
    """Get list of available symbols"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    # Query for unique symbols from table names
    query = """
        SELECT DISTINCT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND (tablename LIKE '%_1m' OR tablename LIKE '%_1m_oanda')
    """
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            
        symbols = set()
        for row in rows:
            table_name = row['tablename']
            # Extract symbol from table name
            if '_oanda' in table_name:
                symbol = table_name.split('_')[0].upper()
            else:
                symbol = table_name.rsplit('_', 1)[0].upper()
            symbols.add(symbol)
            
        return sorted(list(symbols))
        
    except Exception as e:
        logger.error(f"Failed to get symbols: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve symbols")


@app.get("/api/timeframes")
async def get_timeframes() -> List[str]:
    """Get list of available timeframes"""
    return TIMEFRAMES


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "database": "disconnected",
        "timestamp": datetime.now().isoformat()
    }
    
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["database"] = "connected"
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
    
    return health_status


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get API statistics"""
    hit_rate = cache_stats["hits"] / cache_stats["total_requests"] if cache_stats["total_requests"] > 0 else 0
    
    return {
        "cache": {
            "size": len(candle_cache),
            "max_size": CACHE_SIZE,
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "total_requests": cache_stats["total_requests"]
        },
        "database": {
            "pool_size": db_pool.get_size() if db_pool else 0,
            "pool_free": db_pool.get_idle_size() if db_pool else 0
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)