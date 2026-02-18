from quantix_core.database.connection import db
import json

def check_logs():
    print("=== CHECKING SYSTEM LOGS (SUPABASE) ===")
    
    # 1. Validation Events
    v_res = db.client.table('validation_events').select('*').order('created_at', desc=True).limit(5).execute()
    print(f"\n[Validation Events Table] - Found {len(v_res.data)} latest entries")
    for log in v_res.data:
        print(f" - {log.get('created_at')} | {log.get('check_type')} | Signal: {log.get('signal_id')} | Discrepancy: {log.get('is_discrepancy')}")
        if log.get('validator_candle'):
            print(f"   ∟ Proof: {json.dumps(log.get('validator_candle'))[:100]}...")
        else:
            print(f"   ∟ ⚠️ MISSING CANDLE PROOF")

    # 2. AI Machine Heartbeat (Thinking Logs)
    h_res = db.client.table('fx_analysis_log').select('*').order('timestamp', desc=True).limit(5).execute()
    print(f"\n[AI Heartbeat Table] - Found {len(h_res.data)} latest entries")
    for log in h_res.data:
        print(f" - {log.get('timestamp')} | {log.get('asset')} | Status: {log.get('status')} | Conf: {log.get('confidence')}")
        # Check current known keys: ['id', 'timestamp', 'asset', 'price', 'direction', 'confidence', 'status', 'strength']
        if log.get('refinement'):
            print(f"   ∟ Reason: {log.get('refinement')[:80]}...")
        elif log.get('refinement_reason'): # Check alternative name
             print(f"   ∟ Reason: {log.get('refinement_reason')[:80]}...")
        else:
            print(f"   ∟ ⚠️ NO REFINEMENT DATA (Column might be missing in DB)")

    # 3. Recent Signals & Validation Status
    s_res = db.client.table('fx_signals').select('id, asset, direction, entry_price, status, state, result, generated_at').order('generated_at', desc=True).limit(3).execute()
    print(f"\n[Recent Signals] - Found {len(s_res.data)} latest signals")
    for sig in s_res.data:
        print(f" - {sig.get('generated_at')} | {sig.get('id')[:8]} | {sig.get('asset')} | {sig.get('direction')} | Status: {sig.get('status')} | State: {sig.get('state')} | Result: {sig.get('result')}")
        
        # Check if there are any validation events for this signal
        v_events = db.client.table('validation_events').select('*').eq('signal_id', sig.get('id')).execute()
        if v_events.data:
            print(f"   ∟ ✅ FOUND {len(v_events.data)} validation events")
        else:
            print(f"   ∟ ❌ NO validation events found yet")

if __name__ == "__main__":
    check_logs()
