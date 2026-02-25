from quantix_core.database.connection import db
import sys

sig_id = '724e4ad6-be2b-4b15-91f6-5d952fa3c931'

candidates = [
    "TP_HIT", "SL_HIT", "TIME_EXIT",
    "CLOSED", "COMPLETED", "FINISHED",
    "TAKE_PROFIT", "STOP_LOSS",
    "WIN", "LOSS",
    "PROFIT", "LOSS_HIT",
    "EXPIRED", "ARCHIVED",
    "SUCCESS", "FAILED",
    "DONE", "EXITED"
]

for val in candidates:
    try:
        db.client.table("fx_signals").update({"state": val}).eq("id", sig_id).execute()
        print(f"✅ State '{val}' is ALLOWED")
    except Exception as e:
        if "chk_state_valid" in str(e):
            pass # print(f"❌ State '{val}' is INVALID (Constraint)")
        else:
            print(f"❓ State '{val}' failed with OTHER error: {str(e)[:100]}")

print("\nFinal check: What are the current states in DB for ANY signal?")
res = db.client.table("fx_signals").select("state").execute()
all_states = set(s['state'] for s in res.data if s['state'])
print(f"States currently in DB: {all_states}")
