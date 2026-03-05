import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
since = (now - timedelta(hours=1)).isoformat()

# Get ALL recent logs from last hour
res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .gte("timestamp", since)\
    .order("timestamp", desc=True)\
    .limit(30)\
    .execute()

print(f"=== ALL LOGS IN LAST HOUR (UTC: {now.isoformat()}) ===\n")
for r in res.data:
    ts = r["timestamp"]
    asset = r["asset"]
    direction = r["direction"]
    status = str(r["status"])[:70]
    print(f"{ts} | {asset:<20} | {direction:<10} | {status}")

# Check for crash indicators
print("\n=== CRASH/ERROR CHECK ===")
crash_res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .eq("direction", "CRASH")\
    .order("timestamp", desc=True)\
    .limit(5)\
    .execute()

if crash_res.data:
    for r in crash_res.data:
        print(f"🔴 CRASH: {r['timestamp']} | {r['asset']} | {r['status']}")
else:
    print("✅ No CRASH records found")

# Check restart attempts
restart_res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, status")\
    .like("status", "AUTO_RESTART%")\
    .order("timestamp", desc=True)\
    .limit(5)\
    .execute()

if restart_res.data:
    print("\n=== RESTART ATTEMPTS ===")
    for r in restart_res.data:
        print(f"⚠️ {r['timestamp']} | {r['asset']} | {r['status']}")
else:
    print("✅ No restart attempts detected")
