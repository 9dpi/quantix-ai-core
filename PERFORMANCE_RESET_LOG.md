# Performance Reset Log - AUTO v0

## Reset Information

**Date**: 2026-01-30  
**Time**: 11:46 UTC+7  
**Reason**: Implementation of Fixed RR Rule (AUTO v0)

---

## Changes Made

### Previous System (Dynamic TP/SL)
- **TP**: 20 pips (variable based on market conditions)
- **SL**: 15 pips (variable based on market conditions)
- **RRR**: ~1.33:1 (dynamic)

### New System (Fixed TP/SL - AUTO v0)
- **TP**: 10 pips (fixed for all signals)
- **SL**: 10 pips (fixed for all signals)
- **RRR**: 1:1 (fixed)

---

## Previous Performance Summary (Before Reset)

**Data Period**: Unknown start date → 2026-01-30 04:42 UTC  
**Total Signals Analyzed**: 582

| Metric | Value |
|--------|-------|
| Total Signals | 582 |
| Wins | 251 |
| Losses | 331 |
| Win Rate | 43.1% |
| Avg Confidence | 75.95% |
| Peak Confidence | 100% |

### Breakdown by Direction
- **BUY**: 125/268 wins (46.6%)
- **SELL**: 114/238 wins (47.9%)
- **HOLD**: 12/76 wins (15.8%)

---

## Reset Actions

1. ✅ Backed up old `heartbeat_audit.jsonl` (if exists)
2. ✅ Reset `learning_data.json` to zero state
3. ✅ Updated `continuous_analyzer.py` with Fixed TP/SL logic
4. ✅ Documented changes in `FIXED_RR_RULE_v0.md`

---

## New Baseline

Starting fresh with:
- **Total Samples**: 0
- **Total Signals**: 0
- **Win Rate**: 0% (to be calculated)
- **Current Trend**: INITIALIZING

All new signals from this point forward will use the Fixed 10 pips TP/SL rule.

---

## Monitoring Plan

1. **First 50 signals**: Observe win rate with new TP/SL
2. **First 100 signals**: Compare with previous dynamic system
3. **First 200 signals**: Evaluate if Fixed RR is optimal or needs adjustment

---

**Next Review**: After 50 signals with new rule  
**Status**: ✅ Reset Complete
