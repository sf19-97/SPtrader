# SPtrader Documentation Guide
*Created: May 25, 2025 21:02 UTC*

## 📖 How to Use SPtrader Documentation

### For New Sessions

When starting a new Claude session or returning to the project:

1. **First, read these key files:**
   ```bash
   # Check current state
   cat ~/SPtrader/PROJECT_STATUS.md
   
   # See recent changes
   cat ~/SPtrader/docs/SESSION_CHANGELOG.md
   
   # Understand the architecture
   cat ~/SPtrader/README.md
   ```

2. **Verify system state:**
   ```bash
   sptrader status
   sptrader db query "SELECT count(*) FROM market_data_v2"
   ```

### Documentation Map

```
SPtrader/
├── CLAUDE.md                    # Instructions for AI assistants
├── PROJECT_STATUS.md           # Current state & next steps
├── README.md                   # Overview & quick start
├── MIGRATION_GUIDE.md          # Python→Go migration details
├── PROJECT_ORGANIZATION.md     # File structure
├── DOCUMENTATION_GUIDE.md      # This file
└── docs/
    ├── CLI_TUI.md             # How to use interfaces
    ├── ILP_IMPLEMENTATION.md   # Data ingestion guide
    ├── SESSION_CHANGELOG.md    # Recent changes
    ├── DIRECTORY_STRUCTURE.md  # Detailed file layout
    └── DOCUMENTATION_AUDIT.md  # Doc accuracy check

```

### Key Information Locations

| Topic | File | Section |
|-------|------|---------|
| Current data count | PROJECT_STATUS.md | "Data Loading Results" |
| API endpoints | README.md | "SPtrader CLI Guide" |
| Data loading | ILP_IMPLEMENTATION.md | "Loading Data Workflow" |
| Service ports | README.md | "Architecture > Services" |
| Recent changes | SESSION_CHANGELOG.md | Latest session |
| CLI commands | docs/CLI_TUI.md | "CLI Reference" |
| Performance metrics | ILP_IMPLEMENTATION.md | "Performance Metrics" |

### Quick Status Commands

```bash
# System health
sptrader status

# Data volume
sptrader db stats

# API health
sptrader api health

# Recent logs
sptrader logs

# Monitor everything
sptrader monitor
```

### Documentation Standards

1. **Always include timestamps** in format: `May 25, 2025 21:00 UTC`
2. **Update SESSION_CHANGELOG.md** after significant changes
3. **Keep PROJECT_STATUS.md current** with latest state
4. **Mark completed items** with ✅ and pending with ❌

### For AI Assistants

When working on SPtrader:
1. Always check CLAUDE.md first for project-specific rules
2. Read PROJECT_STATUS.md to understand current state
3. Update documentation with timestamps when making changes
4. Use ILP for data ingestion (not HTTP SQL)
5. Reference existing patterns in codebase

### Finding Information

```bash
# Search documentation
grep -r "ILP" ~/SPtrader/*.md ~/SPtrader/docs/*.md

# Find specific topics
grep -r "port 8080" ~/SPtrader/*.md

# List all documentation
find ~/SPtrader -name "*.md" -type f | sort
```