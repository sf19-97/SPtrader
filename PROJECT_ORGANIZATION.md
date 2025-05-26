# SPtrader Project Organization
*Last Updated: May 25, 2025*
*Status: Migration Complete - This document reflects the current organization*

## 📁 Current Root Directory Organization

### Files Currently in Root
These are primary entry points and essential configs:
```
.
├── sptrader              # Main CLI (✅ using Go API)
├── clean_tui.py         # TUI interface (✅ calls CLI)
├── go.mod               # Go module definition  
├── go.sum               # Go dependencies lock
├── Makefile             # Build automation
├── .env                 # Configuration
├── .env.example         # Config template
├── .gitignore           # Git ignore rules
├── README.md            # Main documentation
├── MIGRATION_GUIDE.md   # Migration documentation
├── PROJECT_STATUS.md    # Current project state
├── PROJECT_ORGANIZATION.md  # This file
└── CLAUDE.md            # AI assistant instructions
```

### Operational Scripts (Current Location)
```
├── start_go_services.sh  # ✅ In root (called by CLI)
├── stop_all.sh          # ✅ In root (called by CLI)
├── install_cli.sh       # ❌ Moved to scripts/
├── directory_map.sh     # ❌ Moved to scripts/
```

### Files Already Moved to `/deprecated`
```
/deprecated/
├── python-api/          # ✅ Old FastAPI implementation
├── migration-scripts/   # ✅ Migration helper scripts
├── sexy_minimal_tui.py  # ✅ Old TUI attempt
├── matrix_tui.py       # ✅ Old TUI attempt
└── README.python.md     # ✅ Old Python README
```

### Authentication Files (Still in Root)
```
├── SPtrader-login.py      # Matrix authentication wrapper
├── SPtrader-login.desktop # Desktop launcher
```
*Note: These could be moved to `/auth` for better organization*

### TUI Status
```
├── clean_tui.py  # ✅ Active TUI - kept in root as primary interface
```

## 🏗️ Current Directory Structure

```
SPtrader/
├── cmd/                    # Go applications
│   ├── api/               # Main API server
│   └── profiler/          # Performance profiler
│
├── internal/              # Private Go packages
│   ├── api/              # HTTP handlers
│   ├── config/           # Configuration
│   ├── db/               # Database layer
│   ├── models/           # Domain models
│   └── services/         # Business logic
│
├── api/                   # Python FastAPI (temporary)
├── auth/                  # Authentication wrappers
├── charts/                # Chart assets
├── data_feeds/           # Market data importers
├── deprecated/           # Old code for reference
├── docs/                 # Documentation
├── frontend/             # React app (future)
├── logs/                 # Log files
├── scripts/              # Utility scripts
├── sql/                  # Database scripts
├── tools/                # Management tools
│
├── .env.example          # Configuration template
├── .gitignore           # Git ignore rules
├── go.mod               # Go dependencies
├── Makefile             # Build automation
├── MIGRATION_GUIDE.md   # This guide
├── README.md            # Main documentation
└── sptrader             # Main CLI
```

## ✅ Migration Status

The file reorganization has been completed:
- ✅ Python API moved to `/deprecated/python-api/`
- ✅ Old TUI attempts moved to `/deprecated/`
- ✅ Migration scripts moved to `/deprecated/migration-scripts/`
- ✅ Go structure implemented (`cmd/`, `internal/`)
- ✅ Clean separation between active and deprecated code

## 📝 Documentation Files

### Keep in `/docs`
- `DATA_ARCHITECTURE_PLAN.md`
- `IMPLEMENTATION_ROADMAP.md`
- `PYTHON_VS_GO_COMPARISON.md`
- Technical specifications

### Keep in Root
- `README.md` - Primary documentation
- `MIGRATION_GUIDE.md` - Current transition
- `PROJECT_STATUS.md` - Project state
- `PROJECT_ORGANIZATION.md` - This file

### Already Archived/Merged
- ✅ CLI documentation → merged into `/docs/CLI_TUI.md`
- ✅ Go-specific info → merged into main `README.md`

## 🎯 Decisions Made

1. **TUI Location**: ✅ `clean_tui.py` kept in root as primary UI interface

2. **Script Naming**: ✅ Kept original names for backward compatibility
   - `start_go_services.sh` - clear name for Go services
   - `stop_all.sh` - stops everything

3. **Binary Location**: ✅ Using `/build` directory (gitignored)
   - Binaries compiled to `/build/sptrader-api`
   - Not installed to system PATH

4. **Config Files**: ✅ Kept `.env` in root for simplicity

## 🚀 Benefits of Organization

1. **Cleaner Root** - Only essential files
2. **Clear Purpose** - Each directory has specific role
3. **Easy Navigation** - Logical structure
4. **Migration Path** - Clear what's old vs new
5. **Git History** - Preserves file history with moves

## ✅ Organization Complete

The project reorganization has been successfully completed as of May 25, 2025:
- Go API is primary (Python archived)
- Clear separation of active vs deprecated code
- Documentation updated to reflect current state
- Single control path through CLI

The project structure is now clean, organized, and ready for continued development.