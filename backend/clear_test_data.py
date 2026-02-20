"""
clear_test_data.py -- Remove all test/mock data, keep only real data
====================================================================
Dry run:  python backend/clear_test_data.py
Apply:    python backend/clear_test_data.py --apply

DB schema facts (verified):
  validation_events : id(uuid), signal_id, check_type, created_at
  fx_analysis_log   : id(int),  asset, direction, timestamp, status, strength, confidence, price
  fx_signals        : id(uuid), state, asset, generated_at, is_test
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from quantix_core.database.connection import SupabaseConnection
db = SupabaseConnection()
cl = db.client

APPLY = "--apply" in sys.argv
sep = "-" * 55

print(sep)
print("APPLY MODE" if APPLY else "DRY RUN  (add --apply to delete)")
print(sep); print()

total_deleted = 0

def delete_ids(table, ids):
    if not ids: return
    for i in range(0, len(ids), 100):
        cl.table(table).delete().in_("id", ids[i:i+100]).execute()

# ---------------------------------------------------------------
# 1. validation_events - test records
# ---------------------------------------------------------------
print("[1] validation_events")

hc  = cl.table("validation_events").select("id,signal_id,check_type,created_at").eq("signal_id","__health_check__").execute().data or []
pd  = cl.table("validation_events").select("id,signal_id,check_type,created_at").eq("check_type","PRE_DEPLOY_TEST").execute().data or []
tv  = {r['id']: r for r in hc + pd}

print(f"  __health_check__ rows : {len(hc)}")
print(f"  PRE_DEPLOY_TEST rows  : {len(pd)}")
print(f"  Total to remove       : {len(tv)}")
for r in list(tv.values())[:5]:
    print(f"    {str(r['id'])[:12]}... | {r['check_type']} | {str(r['created_at'])[:19]}")

if APPLY and tv:
    delete_ids("validation_events", list(tv.keys()))
    print(f"  DELETED: {len(tv)}")
    total_deleted += len(tv)

after = cl.table("validation_events").select("id").execute().data or []
print(f"  Remaining: {len(after)}\n")

# ---------------------------------------------------------------
# 2. fx_analysis_log - AUTO_ADJUSTER test entries
# ---------------------------------------------------------------
print("[2] fx_analysis_log")

adj = cl.table("fx_analysis_log").select("id,asset,direction,timestamp,status").eq("asset","AUTO_ADJUSTER").execute().data or []
tl  = {r['id']: r for r in adj}

print(f"  AUTO_ADJUSTER entries : {len(adj)}")
print(f"  Total to remove       : {len(tl)}")
for r in list(tl.values())[:4]:
    ts = str(r.get('timestamp','?'))[:19]
    print(f"    id={r['id']} | {r['direction']} | {ts}")

if APPLY and tl:
    delete_ids("fx_analysis_log", list(tl.keys()))
    print(f"  DELETED: {len(tl)}")
    total_deleted += len(tl)

after_l = cl.table("fx_analysis_log").select("id").execute().data or []
print(f"  Remaining: {len(after_l)}\n")

# ---------------------------------------------------------------
# 3. fx_signals - is_test=true rows
# ---------------------------------------------------------------
print("[3] fx_signals")

# is_test column exists
try:
    test_true = cl.table("fx_signals").select("id,state,asset,generated_at").eq("is_test",True).execute().data or []
except Exception:
    test_true = []

# state=TEST or state=MOCK (non-standard states)
try:
    st_   = cl.table("fx_signals").select("id,state,asset,generated_at").eq("state","TEST").execute().data or []
    sm_   = cl.table("fx_signals").select("id,state,asset,generated_at").eq("state","MOCK").execute().data or []
except Exception:
    st_ = sm_ = []

tsg = {r['id']: r for r in test_true + st_ + sm_}

print(f"  is_test=true : {len(test_true)}")
print(f"  state=TEST   : {len(st_)}")
print(f"  state=MOCK   : {len(sm_)}")
print(f"  Total to remove: {len(tsg)}")
for r in list(tsg.values())[:5]:
    print(f"    {r['id']} | {r['state']} | {r['asset']} | {str(r.get('generated_at','?'))[:19]}")

if APPLY and tsg:
    delete_ids("fx_signals", list(tsg.keys()))
    print(f"  DELETED: {len(tsg)}")
    total_deleted += len(tsg)

after_s = cl.table("fx_signals").select("id").execute().data or []
print(f"  Remaining: {len(after_s)}\n")

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
print(sep)
total_would = len(tv) + len(tl) + len(tsg)
if APPLY:
    print(f"DONE -- Deleted {total_deleted} test/mock records. DB = real data only.")
else:
    print(f"DRY RUN -- Would delete {total_would} records. Run --apply to execute.")
print(sep)
