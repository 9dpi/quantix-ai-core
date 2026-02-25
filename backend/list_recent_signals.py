from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
res = db.client.table("fx_signals").select("*").gte("generated_at", since).order("generated_at", desc=True).limit(20).execute()

print(f"{'ID':<10} | {'Asset':<7} | {'State':<15} | {'Entry':<8} | {'TP':<8} | {'SL':<8} | {'Status':<15}")
print("-" * 80)
for s in res.data:
    print(f"{s['id'][:8]:<10} | {s['asset']:<7} | {s['state']:<15} | {s['entry_price']:<8} | {s['tp']:<8} | {s['sl']:<8} | {s['status']:<15}")
