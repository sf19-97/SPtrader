# SPtrader CLI & TUI Documentation

## Overview

SPtrader provides two interfaces for managing the forex trading platform:
- **CLI (`sptrader`)**: Command-line interface for power users and automation
- **TUI (`clean_tui.py`)**: Terminal User Interface with visual menus

Both interfaces control the same underlying system through a unified architecture:
```
Scripts (start_go_services.sh, etc.)
    ↑
   CLI (sptrader) ← Single control point
    ↑
   TUI (clean_tui.py) ← Visual wrapper
```

## CLI Reference

### Installation
```bash
# Add sptrader to your PATH
./scripts/install_cli.sh

# Or manually:
sudo ln -s ~/SPtrader/sptrader /usr/local/bin/sptrader
```

### Core Commands

#### Service Management
```bash
sptrader start      # Start all services (QuestDB, Go API, data feeds)
sptrader stop       # Stop all services gracefully
sptrader restart    # Stop and restart all services
sptrader status     # Check health of all services
```

#### Monitoring & Logs
```bash
sptrader monitor    # Real-time dashboard (interactive)
sptrader logs       # Show recent log entries
sptrader logs -f    # Follow all logs in real-time
sptrader logs show  # Display log status and sizes
sptrader logs clean # Clean logs (all|runtime|status|archive)
sptrader logs tail <service>  # Follow specific service log
```

#### API Commands
```bash
sptrader api health # Check API connectivity
sptrader api stats  # View cache and performance metrics
sptrader api docs   # Open API documentation (browser)
sptrader api test   # Run API test suite
```

#### Database Commands
```bash
sptrader db console        # Open QuestDB web console
sptrader db query "<SQL>"  # Execute SQL query
sptrader db stats          # View data statistics
```

#### Maintenance
```bash
sptrader optimize   # Run QuestDB viewport optimizations
sptrader test       # Run all tests
sptrader test api   # Run API tests only
sptrader test connectivity  # Test external connections
```

### Usage Examples

```bash
# Daily workflow
sptrader start              # Start trading platform
sptrader monitor            # Watch real-time status
sptrader logs -f            # Debug issues

# Data management
sptrader db query "SELECT count(*) FROM ohlc_5m_v2"
sptrader db stats           # Check data volumes
sptrader optimize           # Optimize query performance

# Troubleshooting
sptrader status             # What's running?
sptrader api health         # Is API responding?
sptrader logs tail oanda_feed  # Check specific service
```

### Environment Variables
The CLI respects these environment variables:
- `SPTRADER_HOME`: Base directory (default: `~/SPtrader`)
- `DATABASE_URL`: QuestDB connection string
- `GIN_MODE`: Go API mode (debug|release)

## TUI Reference

### Starting the TUI
```bash
# Direct execution
python3 ~/SPtrader/clean_tui.py

# Or if in SPtrader directory
./clean_tui.py
```

### Main Menu Options

1. **[1] Start All Services**
   - Executes: `sptrader start`
   - Starts QuestDB, Go API, and data feeds

2. **[2] Stop All Services**
   - Executes: `sptrader stop`
   - Gracefully stops all components

3. **[3] Restart Services**
   - Executes: `sptrader restart`
   - Stops then starts all services

4. **[4] Check Status**
   - Executes: `sptrader status`
   - Shows health of each service

5. **[5] View Logs**
   - Shows last 20 lines of runtime logs
   - Filtered for readability

6. **[6] API Health**
   - Executes: `curl http://localhost:8080/api/v1/health`
   - Shows API connection status

7. **[7] Database Stats**
   - Queries record count from QuestDB
   - Shows data volume

8. **[M] Monitor Mode**
   - Real-time service monitoring
   - Updates every 2 seconds
   - Shows service status and API health
   - Press 'q' to exit monitor mode

9. **[Q] Quit**
   - Exit the TUI

### TUI Features

- **Color-coded output**: Green=running, Red=stopped, Yellow=warning
- **Centered display**: Adapts to terminal size
- **Simple navigation**: Single-key commands
- **Visual feedback**: Clear status messages
- **Monitor mode**: Real-time updates without leaving TUI

### Architecture Integration

The TUI is a thin wrapper around the CLI:
```python
# TUI calls CLI commands
os.system('./sptrader start')
os.system('./sptrader stop')
os.system('./sptrader status')
```

This ensures:
- Consistent behavior between interfaces
- Single source of truth for operations
- Easier maintenance

## Service Architecture

### Components Started
1. **QuestDB** (Port 9000)
   - Time-series database
   - Web console at http://localhost:9000

2. **Go API** (Port 8080)
   - REST API using Gin framework
   - Endpoints at http://localhost:8080/api/v1/
   - Health check: http://localhost:8080/api/v1/health

3. **Data Feeds**
   - Oanda real-time feed (Python)
   - OHLC aggregation manager (Python)

### Log Locations
```
~/SPtrader/logs/
├── runtime/          # Active service logs
│   ├── oanda_feed.log
│   ├── ohlc_manager.log
│   └── questdb.log
├── status/           # Health check logs
│   └── connectivity_test.log
└── archive/          # Rotated logs
```

## Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   sptrader status  # Check what's already running
   sptrader logs tail questdb  # Check for port conflicts
   ```

2. **API not responding**
   ```bash
   sptrader api health  # Check basic connectivity
   ps aux | grep sptrader-api  # Is process running?
   ```

3. **TUI commands fail**
   - Ensure CLI is in PATH: `which sptrader`
   - Check permissions: `ls -la ~/SPtrader/sptrader`

### Debug Mode
```bash
# Run with debug output
GIN_MODE=debug sptrader start

# Check all logs
sptrader logs -f
```

## Migration Notes

As of May 25, 2025, the system has migrated from Python (FastAPI) to Go (Gin):
- Old: Python API on port 8000
- New: Go API on port 8080
- All interfaces now use the Go API
- Python components remaining: data feeds only

## Quick Reference Card

```
SERVICE CONTROL          MONITORING              DATA MANAGEMENT
sptrader start          sptrader monitor        sptrader db console
sptrader stop           sptrader logs -f        sptrader db query "..."
sptrader restart        sptrader logs show      sptrader db stats
sptrader status         sptrader api health     sptrader optimize

TESTING                 HELP
sptrader test all       sptrader help
sptrader test api       sptrader --help
sptrader api test       man sptrader (if installed)
```

## Future Enhancements

- [ ] Web UI interface
- [ ] Mobile app control
- [ ] Remote management API
- [ ] Service auto-recovery
- [ ] Performance profiling commands
- [ ] Backup/restore utilities