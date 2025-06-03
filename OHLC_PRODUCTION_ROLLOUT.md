# OHLC Production Rollout Checklist
*Created: May 31, 2025*

## Overview
This document outlines the process for rolling out the fixed OHLC generation pipeline to production. The new implementation directly samples from tick data for all timeframes, preventing the data integrity issues observed in the previous implementation.

## Pre-Deployment Tasks

### Backups
- [ ] Create a full database backup before starting
  ```bash
  pg_dump questdb > questdb_final_backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Verify the backup is complete and restorable
- [ ] Store backup in at least two locations

### Environment Verification
- [ ] Verify QuestDB is running and accessible
  ```bash
  curl http://localhost:9000/exec?query=SELECT%201
  ```
- [ ] Verify adequate disk space for new OHLC tables
- [ ] Check market_data_v2 has expected tick data
  ```bash
  curl "http://localhost:9000/exec?query=SELECT+COUNT(*)+FROM+market_data_v2+WHERE+symbol='EURUSD'"
  ```

## Rollout Process - One Symbol at a Time

### Step 1: EURUSD (Initial Test Symbol)
- [ ] Run production OHLC generator for EURUSD only
  ```bash
  cd /home/millet_frazier/SPtrader
  python3 scripts/production_ohlc_generator.py EURUSD
  ```
- [ ] Verify data integrity with verification script
  ```bash
  python3 scripts/production_ohlc_verification.py EURUSD
  ```
- [ ] Manually check expected candle counts:
  ```
  1m: ~1,430 candles per day
  5m: ~288 candles per day
  15m: ~96 candles per day
  30m: ~48 candles per day
  1h: ~24 candles per day
  4h: ~6 candles per day
  1d: ~1 candle per day
  ```
- [ ] Check for any duplicate timestamps
- [ ] Check for any weekend timestamps in daily candles
- [ ] Verify candle data continuity between timeframes

### Step 2: GBPUSD (Second Symbol)
- [ ] Run production OHLC generator for GBPUSD
  ```bash
  python3 scripts/production_ohlc_generator.py GBPUSD
  ```
- [ ] Verify data integrity with verification script
  ```bash
  python3 scripts/production_ohlc_verification.py GBPUSD
  ```
- [ ] Perform same checks as with EURUSD

### Step 3: USDJPY (Third Symbol)
- [ ] Run production OHLC generator for USDJPY
  ```bash
  python3 scripts/production_ohlc_generator.py USDJPY
  ```
- [ ] Verify data integrity with verification script
  ```bash
  python3 scripts/production_ohlc_verification.py USDJPY
  ```
- [ ] Perform same checks as with previous symbols

### Step 4: Remaining Symbols
- [ ] Proceed with other symbols only after first three are verified
- [ ] Consider running in batches with verification between each batch

## Post-Deployment Verification

### Chart Verification
- [ ] Check charts in frontend for EURUSD to ensure:
  - No gaps in data
  - Proper candle formation
  - Correct timeframe transitions
- [ ] Repeat for other symbols

### Monitoring Setup
- [ ] Set up daily monitoring script
- [ ] Configure alerts for data integrity issues
- [ ] Schedule weekly full verification

## Rollback Procedure (If Needed)

### Criteria for Rollback
- Missing candles compared to expected counts
- Duplicate timestamps detected
- Incorrect weekend handling
- Frontend chart display issues
- Data verification script failures

### Rollback Steps
1. Stop any running OHLC generation processes
2. Restore database from backup
   ```bash
   psql questdb < questdb_backup_filename.sql
   ```
3. Notify team of rollback and reason
4. Document issues encountered

## Escalation Contacts

**Primary Contact:** [Your Name] - [Your Email/Phone]

**Secondary Contacts:**
- Database Administrator: [Name] - [Email/Phone]
- Backend Team Lead: [Name] - [Email/Phone]
- Frontend Team Lead: [Name] - [Email/Phone]

## Success Criteria

The rollout will be considered successful when:
1. All symbols have been processed without errors
2. Verification script passes for all symbols
3. Frontend charts display correctly without gaps
4. Daily monitoring shows consistent candle counts
5. No duplicate timestamps or weekend irregularities detected

## Documentation

Ensure the following documentation is updated:
- System architecture diagrams
- Data flow documentation
- Monitoring documentation
- Troubleshooting guide

---

*This document was created as part of the OHLC data pipeline rebuild project.*