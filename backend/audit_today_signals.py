from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta
import json

today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
res = db.client.table("fx_signals").select("*").gte("generated_at", today.isoformat()).order("generated_at", desc=False).execute()

output = {
    "report_date": str(today.date()),
    "signals": [],
    "summary": {}
}

if res.data:
    for s in res.data:
        output["signals"].append({
            "time": s['generated_at'],
            "id": s['id'],
            "side": s.get('direction'),
            "entry": s.get('entry_price'),
            "state": s.get('state'),
            "status": s.get('status'),
            "result": s.get('result')
        })
    
    # Calculate counts
    output["summary"] = {
        "total": len(res.data),
        "tp": len([s for s in res.data if s['status'] == 'CLOSED_TP']),
        "sl": len([s for s in res.data if s['status'] == 'CLOSED_SL']),
        "expired": len([s for s in res.data if s['status'] == 'EXPIRED']),
        "timeout": len([s for s in res.data if s['status'] == 'CLOSED_TIMEOUT']),
        "active": len([s for s in res.data if s['state'] in ['WAITING_FOR_ENTRY', 'ENTRY_HIT']])
    }

with open("backend/audit_today.json", "w") as f:
    json.dump(output, f, indent=2)

print("Report saved to backend/audit_today.json")
