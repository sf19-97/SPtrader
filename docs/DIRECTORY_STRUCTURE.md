# SPtrader Directory Structure

## Overview

This document describes the organized directory structure of the SPtrader project. All scripts and files are logically grouped by function.

## Directory Structure

```
SPtrader/
├── api/                        # FastAPI backend
│   ├── main.py                # API endpoints and server
│   ├── test_api.py            # API test suite
│   └── test_viewport.py       # Viewport functionality tests
│
├── data_feeds/                 # Data import and feed scripts
│   ├── oanda_feed.py          # Real-time Oanda data feed
│   ├── dukascopy_importer.py  # Historical data importer
│   └── historical_backfill.py # Historical data management
│
├── scripts/                    # Core service scripts
│   ├── ohlc_manager.py        # OHLC aggregation service
│   ├── cors_proxy.py          # CORS proxy (legacy)
│   ├── execute_questdb_optimizations.py  # Run DB optimizations
│   └── update_data_tables_source_tracking.py  # Add data source tracking
│
├── tools/                      # Management and monitoring tools
│   ├── check_services.sh      # Service health checker
│   ├── monitor.sh             # Real-time monitoring dashboard
│   ├── test_connectivity.sh   # External service connectivity tests
│   ├── manage_logs.sh         # Log management system
│   ├── complete_data_source_update.sh  # Data source setup
│   └── dashboard.sh           # Legacy dashboard (deprecated)
│
├── sql/                        # SQL scripts
│   └── optimize_questdb.sql   # Viewport optimization queries
│
├── frontend/                   # React frontend (to be implemented)
│   ├── src/
│   └── package.json           # Currently empty
│
├── logs/                       # Log files (organized)
│   ├── runtime/               # Service logs (append)
│   ├── status/                # Status logs (overwrite)
│   └── archive/               # Compressed historical logs
│
├── docs/                       # Documentation
│   ├── LOG_MANAGEMENT.md      # Log system documentation
│   └── DIRECTORY_STRUCTURE.md # This file
│
├── deprecated/                 # Old/legacy files
│   ├── forex_chart.html       # Old charting implementation
│   └── test.html              # Test file
│
├── Root Control Scripts        # Main control scripts stay in root
├── sptrader                   # CLI wrapper executable
├── install_cli.sh             # CLI installation script
├── start_background.sh        # Service startup script
├── stop_all.sh                # Service shutdown script
├── CLAUDE.md                  # AI assistant instructions
├── README.md                  # Project documentation
└── PROJECT_STATUS.md          # Current project status
```

## Script Categories

### 1. **Core Services** (`scripts/`)
- Database management and optimization
- Data aggregation
- Service utilities

### 2. **Data Feeds** (`data_feeds/`)
- Real-time market data (Oanda)
- Historical data import (Dukascopy)
- Backfill utilities

### 3. **Management Tools** (`tools/`)
- Service monitoring
- Health checks
- Log management
- System utilities

### 4. **API Backend** (`api/`)
- REST API server
- Test suites
- Performance tests

### 5. **SQL Scripts** (`sql/`)
- Database schemas
- Optimization queries
- Migration scripts

### 6. **Root Scripts**
These remain in root for easy access:
- `sptrader` - Main CLI interface
- `start_background.sh` - Start all services
- `stop_all.sh` - Stop all services
- `install_cli.sh` - Install CLI command

## File Naming Conventions

- Python scripts: `snake_case.py`
- Shell scripts: `snake_case.sh`
- SQL files: `snake_case.sql`
- Documentation: `UPPER_CASE.md`
- Config files: `lower_case.json` or `.conf`

## Best Practices

1. **New Scripts**: Place in appropriate subdirectory
2. **Utilities**: Shell scripts go in `tools/`, Python in `scripts/`
3. **Documentation**: Update when adding new files
4. **Deprecation**: Move old files to `deprecated/` instead of deleting
5. **Logs**: Use structured log directories (runtime/status/archive)

## Future Additions

- `config/` - Configuration files
- `tests/` - Comprehensive test suites
- `migrations/` - Database migrations
- `docker/` - Docker configurations
- `strategies/` - Trading strategies (when implemented)