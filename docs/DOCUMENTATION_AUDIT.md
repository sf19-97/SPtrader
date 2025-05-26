# SPtrader Documentation Audit Report
*Generated: May 25, 2025*

## Summary
This audit identifies which documentation files are accurate and which need updates following the Python→Go migration.

## ❌ OUTDATED FILES (Need Updates)

### 1. `/PROJECT_STATUS.md`
**Issues:**
- Line 29-31: Says "Next: Update CLI and TUI" but this is already done
- Line 107: References port 8000 for API (should be 8080)
- Line 246: Says "FastAPI: 8000" (should say "Go API: 8080")
- Line 254: References "fastapi.log" (should be Go API logs)
- Line 269: Mentions "Frontend package.json is empty" as issue
- Line 274: Still references "Oanda feed failing" which may be resolved

### 2. `/MIGRATION_GUIDE.md`
**Issues:**
- Line 12-13: Says CLI/TUI are "Ready to update" but they're already updated
- Line 20: Says sptrader "will be updated" but it's already updated
- Line 33: References "start_background.sh" which no longer exists
- The whole "Migration Steps" section (lines 60-91) presents future steps as if not done

### 3. `/README.md`
**Major Issues:**
- Has duplicate sections (lines 20-28 repeated)
- Line 35: References port 8000 (should be 8080)
- Line 98: Says "FastAPI" backend (should be "Go API")
- Mixed references to both Python and Go throughout
- Inconsistent port numbers

### 4. `/PROJECT_ORGANIZATION.md`
**Issues:**
- Line 22: References "start_background.sh" which doesn't exist
- Line 34: Plans to move "start_background.sh" but it's already gone
- Presents reorganization as future plan, not current state

## ✅ CORRECT FILES (Accurate)

### 1. `/docs/CLI_TUI.md`
**Status:** ✅ CORRECT
- Created today (May 25, 2025)
- Accurately describes current architecture
- Correctly shows Go API on port 8080
- Properly documents TUI calling CLI commands

### 2. `/CLAUDE.md`
**Status:** ✅ CORRECT (for its purpose)
- Contains project-specific instructions for Claude
- Recently updated with critical dating rule
- FastAPI specification is historical context

### 3. `/docs/SESSION_CHANGELOG.md`
**Status:** ✅ CORRECT
- Historical record of changes
- Doesn't claim to be current state

### 4. `/docs/TUI_SPECIFICATION.md`
**Status:** ✅ MOSTLY CORRECT
- Describes TUI design accurately
- Some implementation details may have changed

### 5. `/docs/LOG_MANAGEMENT.md`
**Status:** ✅ CORRECT
- Log structure and management unchanged
- Still accurate for current system

### 6. `/docs/DIRECTORY_STRUCTURE.md`
**Status:** ✅ CORRECT
- Describes actual directory layout
- Not affected by API migration

## 📋 Files Needing Review

### 1. `/chart-user-workflow.md`
- Need to check if it references correct API endpoints

### 2. `/docs/DATA_ARCHITECTURE_PLAN.md`
- May reference Python API specifics

### 3. `/docs/IMPLEMENTATION_ROADMAP.md`
- Likely outdated timeline/plans

### 4. `/docs/PYTHON_VS_GO_COMPARISON.md`
- Should be accurate but may need updates

## 🔧 Recommended Actions

1. **Update PROJECT_STATUS.md**
   - Remove "Next: Update CLI and TUI" section
   - Change all port 8000 references to 8080
   - Update API references from FastAPI to Go API
   - Mark migration as complete

2. **Update MIGRATION_GUIDE.md**
   - Change CLI/TUI status from "Ready to update" to "✅ Updated"
   - Remove references to non-existent scripts
   - Move migration steps to past tense or mark complete

3. **Fix README.md**
   - Remove duplicate sections
   - Standardize on port 8080
   - Remove mixed Python/Go references
   - Make it consistently about Go implementation

4. **Archive PROJECT_ORGANIZATION.md**
   - Move to /docs/archive/ since reorganization is complete
   - Or update to reflect current state

## 📊 Statistics
- Total documentation files: 14
- Outdated files: 4 (29%)
- Correct files: 6 (43%)
- Need review: 4 (29%)

## 🎯 Priority
1. Fix README.md first (user-facing)
2. Update PROJECT_STATUS.md (main status doc)
3. Update MIGRATION_GUIDE.md (confusing if wrong)
4. Archive or update PROJECT_ORGANIZATION.md