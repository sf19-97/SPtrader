# ILP (InfluxDB Line Protocol) Implementation Guide
*Created: May 25, 2025 20:52 UTC*

## Overview

SPtrader now uses QuestDB's ILP over TCP for high-performance data ingestion, replacing the slower HTTP-based SQL inserts. This document describes the implementation and usage.

## Why ILP?

### Previous Method (HTTP SQL) ❌
- Failed with batches > 3,000 records
- Connection reset errors
- Slow performance
- Query size limitations

### New Method (ILP over TCP) ✅
- Successfully handles 70,000+ records
- ~37,000 ticks/second throughput
- No query size limits
- Built for time-series data

## Architecture

```
Dukascopy API
    ↓
Python Downloader (dukascopy_importer.py)
    ↓
Python Bridge (dukascopy_to_ilp.py)
    ↓ [JSON via stdin]
Go Ingestion Service (cmd/ingestion/main.go)
    ↓ [ILP over TCP]
QuestDB (port 9009)
```

## Components

### 1. Go Ingestion Service (`/cmd/ingestion/main.go`)

The core ILP client that connects to QuestDB on port 9009.

**Features:**
- Test data generation mode
- JSON file import
- Python stdin bridge
- Automatic batching (1,000 records)
- Progress reporting

**Usage:**
```bash
# Generate test data
./build/ingestion -test

# Import from JSON file
./build/ingestion -file data.json

# Accept data from Python (via pipe)
./build/ingestion -python
```

### 2. Python-ILP Bridge (`/data_feeds/dukascopy_to_ilp.py`)

Connects the existing Dukascopy downloader to the Go ILP service.

**Usage:**
```bash
# Download and ingest one day of data
python3 dukascopy_to_ilp.py EURUSD 2024-01-22 2024-01-23

# Download a week
python3 dukascopy_to_ilp.py EURUSD 2024-01-15 2024-01-22
```

### 3. ILP Protocol Details

**Connection:**
- Protocol: TCP
- Host: localhost
- Port: 9009 (default QuestDB ILP port)
- Format: InfluxDB Line Protocol

**Data Format:**
```
market_data_v2,symbol=EURUSD bid=1.0883,ask=1.0884,price=1.08835,spread=0.0001,volume=5.4 1705665600000000000
```

## Performance Metrics

*Measured on May 25, 2025*

| Method | Records | Time | Throughput | Status |
|--------|---------|------|------------|---------|
| HTTP SQL | 3,761 | Failed | N/A | ❌ Connection reset |
| ILP TCP | 3,600 | <1s | ~4,000/sec | ✅ Success |
| ILP TCP | 74,575 | 2s | ~37,000/sec | ✅ Success |

## Building the Ingestion Service

```bash
cd ~/SPtrader
go build -o build/ingestion cmd/ingestion/main.go
```

## Loading Data Workflow

### 1. Start Services
```bash
sptrader start
```

### 2. Load Historical Data
```bash
cd ~/SPtrader/data_feeds

# Load one week of EURUSD
python3 dukascopy_to_ilp.py EURUSD 2024-01-15 2024-01-22

# Load multiple symbols
for symbol in EURUSD GBPUSD USDJPY; do
    python3 dukascopy_to_ilp.py $symbol 2024-01-15 2024-01-22
done
```

### 3. Generate OHLC Data
```bash
python3 -c "
from dukascopy_importer import DukascopyDownloader
d = DukascopyDownloader()
d.generate_ohlcv()
"
```

### 4. Verify Data
```bash
# Check tick count
sptrader db query "SELECT count(*) FROM market_data_v2"

# Check OHLC data
sptrader db query "SELECT count(*) FROM ohlc_1m_v2"

# Test API
curl "http://localhost:8080/api/v1/candles?symbol=EURUSD&tf=1h&start=2024-01-15T00:00:00Z&end=2024-01-16T00:00:00Z"
```

## Troubleshooting

### ILP Connection Failed
- Check QuestDB is running: `sptrader status`
- Verify port 9009 is open: `netstat -an | grep 9009`
- Check QuestDB logs for ILP errors

### No Data After Loading
- Verify date range has market data (not weekends)
- Check Dukascopy cache: `ls ~/SPtrader/data_feeds/dukascopy_cache/`
- Enable debug logging in Python script

### Performance Issues
- Increase batch size in Go service (default: 1,000)
- Check QuestDB memory settings
- Monitor disk I/O during ingestion

## Configuration

### QuestDB ILP Settings
Default configuration should work. If needed, adjust in `questdb.conf`:
```properties
line.tcp.enabled=true
line.tcp.net.bind.to=0.0.0.0:9009
line.tcp.io.worker.count=2
```

### Go Client Settings
Configured in `cmd/ingestion/main.go`:
- Batch size: 1,000 records
- Flush interval: Every batch
- Timeout: 30 seconds

## Future Enhancements

1. **Parallel Ingestion**
   - Multiple symbols simultaneously
   - Worker pool for downloads

2. **Real-time Streaming**
   - Connect Oanda feed directly to ILP
   - Sub-second latency

3. **Data Validation**
   - Price sanity checks
   - Gap detection
   - Quality metrics

4. **Monitoring**
   - Ingestion rate dashboard
   - Error tracking
   - Data completeness reports

## References

- [QuestDB ILP Documentation](https://questdb.io/docs/reference/api/ilp/overview/)
- [Go QuestDB Client](https://github.com/questdb/go-questdb-client)
- [InfluxDB Line Protocol Spec](https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/)