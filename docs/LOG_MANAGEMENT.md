# SPtrader Log Management System

## Overview

SPtrader uses a structured logging system that separates different types of logs for clarity and efficient management. This document explains the logging architecture and how to use the log management tools.

## Log Directory Structure

```
~/SPtrader/logs/
├── runtime/              # Continuous service logs (append mode)
│   ├── questdb.log      # QuestDB database logs
│   ├── fastapi.log      # FastAPI backend logs
│   ├── oanda_feed.log   # Oanda real-time feed logs
│   ├── ohlc_manager.log # OHLC aggregation logs
│   └── frontend.log     # React frontend logs
│
├── status/               # Status snapshots (overwrite mode)
│   ├── connectivity_test.log  # Latest connectivity test results
│   ├── startup_summary.log    # Latest startup summary
│   └── last_error.log        # Most recent error details
│
└── archive/              # Compressed historical logs
    └── runtime_logs_YYYYMMDD_HHMMSS.tar.gz
```

## Log Types

### Runtime Logs (Append Mode)
- **Purpose**: Continuous service output for debugging and monitoring
- **Behavior**: New entries are appended; logs grow over time
- **Location**: `logs/runtime/`
- **Examples**: Service errors, data processing info, API requests

### Status Logs (Overwrite Mode)
- **Purpose**: Latest status snapshots for quick checks
- **Behavior**: Completely replaced on each update
- **Location**: `logs/status/`
- **Examples**: Connectivity tests, health checks, startup summaries

### Archive Logs
- **Purpose**: Historical logs for compliance and analysis
- **Behavior**: Compressed runtime logs rotated periodically
- **Location**: `logs/archive/`
- **Retention**: Last 7 archives kept by default

## Log Management Commands

### View Log Status
```bash
# Show all log information (sizes, ages, locations)
sptrader logs show

# Show recent entries from all logs
sptrader logs

# Follow runtime logs in real-time
sptrader logs -f
```

### Clean Logs
```bash
# Clean all logs (asks for confirmation)
sptrader logs clean all

# Clean only runtime logs
sptrader logs clean runtime

# Clean only status logs
sptrader logs clean status

# Clean archives (asks for confirmation)
sptrader logs clean archive
```

### Rotate Logs
```bash
# Archive logs > 10MB or older than 24 hours
sptrader logs rotate
```

This command:
- Creates compressed archive: `runtime_logs_YYYYMMDD_HHMMSS.tar.gz`
- Clears the original log files
- Keeps only the last 7 archives
- Preserves log history while freeing disk space

### Follow Specific Log
```bash
# Tail a specific log file
sptrader logs tail oanda_feed
sptrader logs tail fastapi
```

## Log Rotation Strategy

### Automatic Rotation Triggers
- Log file size > 10MB
- Log file age > 24 hours
- Manual rotation via `sptrader logs rotate`

### What Gets Rotated
- All files in `logs/runtime/`
- Creates timestamped archive in `logs/archive/`
- Original logs are cleared (not deleted)

### Archive Management
- Keeps last 7 archives by default
- Older archives automatically deleted
- Archives are compressed with gzip

## Best Practices

### 1. Regular Maintenance
```bash
# Weekly rotation recommended
sptrader logs rotate

# Check log sizes regularly
sptrader logs show
```

### 2. Debugging Workflows
```bash
# Start services and watch logs
sptrader start
sptrader logs -f

# Check specific service
sptrader logs tail oanda_feed

# View connectivity status
cat ~/SPtrader/logs/status/connectivity_test.log
```

### 3. Disk Space Management
```bash
# Check total log usage
du -sh ~/SPtrader/logs/

# Clean old runtime logs
sptrader logs clean runtime

# Remove all archives
sptrader logs clean archive
```

### 4. Error Investigation
```bash
# Check latest errors
grep ERROR ~/SPtrader/logs/runtime/*.log | tail -20

# Find errors in specific timeframe
grep "2025-05-24.*ERROR" ~/SPtrader/logs/runtime/oanda_feed.log
```

## Log Levels and Formats

### Service Logs Format
Most services use this format:
```
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```

Example:
```
2025-05-24 10:30:45 - INFO - Successfully connected to QuestDB
2025-05-24 10:30:46 - ERROR - Oanda API authentication failed
```

### Common Log Levels
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Failures requiring attention
- **DEBUG**: Detailed debugging information

## Troubleshooting

### Logs Not Appearing
1. Check service is running: `sptrader status`
2. Verify log directory exists: `ls -la ~/SPtrader/logs/runtime/`
3. Check permissions: `ls -la ~/SPtrader/logs/`

### Logs Growing Too Large
1. Run rotation: `sptrader logs rotate`
2. Adjust rotation frequency in cron
3. Clean old archives: `sptrader logs clean archive`

### Can't Find Specific Error
1. Search across all logs: `grep -r "error message" ~/SPtrader/logs/`
2. Check archives: `zgrep "error message" ~/SPtrader/logs/archive/*.tar.gz`

## Integration with Monitoring

The log system integrates with:
- `sptrader monitor` - Shows latest log entries
- `sptrader status` - Checks log locations
- Startup scripts - Automatic log directory creation

## Environment Variables

You can customize log behavior with:
```bash
export SPTRADER_LOG_RETENTION=14  # Keep 14 archives instead of 7
export SPTRADER_LOG_MAX_SIZE=50M  # Rotate at 50MB instead of 10MB
```

## Future Enhancements

Planned improvements:
- Log shipping to centralized service
- Real-time log analysis
- Automated error alerting
- Performance metrics extraction