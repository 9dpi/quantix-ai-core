import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

def check_signals():
    print("=== LAST 5 SIGNALS IN DB ===")
    res = db.client.table("fx_signals")\
        .select("generated_at, asset, direction, ai_confidence")\
        .order("generated_at", desc=True)\
        .limit(5)\
        .execute()
    
    for r in res.data:
        print(f"[{r['generated_at']}] {r['asset']} | {r['direction']} | Conf: {r['ai_confidence']}")

if __name__ == "__main__":
    check_signals()
