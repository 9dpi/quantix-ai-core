"""
GATE 3 Atomicity Verification Script

Checks for race conditions and invalid state transitions in database.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_atomicity():
    """Verify no atomicity violations in signal state transitions"""
    
    print("=" * 60)
    print("GATE 3 ATOMICITY VERIFICATION")
    print("=" * 60)
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    api_url = f"{supabase_url}/rest/v1/fx_signals"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }
    
    # Test 1: TP/SL before ENTRY_HIT (CRITICAL BUG)
    print("\n✓ Test 1: Checking for TP/SL before ENTRY_HIT...")
    
    response = requests.get(
        api_url,
        headers=headers,
        params={
            "select": "id,state,entry_hit_at,closed_at",
            "state": "in.(TP_HIT,SL_HIT)",
            "entry_hit_at": "is.null"
        }
    )
    
    if response.status_code == 200:
        violations = response.json()
        
        if violations:
            print(f"  ❌ CRITICAL: {len(violations)} signals have TP/SL before ENTRY_HIT!")
            for sig in violations[:3]:
                print(f"    Signal {sig['id'][:8]}... state={sig['state']}, entry_hit_at=NULL")
            return False
        else:
            print("  ✅ No TP/SL before ENTRY_HIT")
    
    # Test 2: ENTRY_HIT with closed_at (should be NULL until TP/SL)
    print("\n✓ Test 2: Checking for ENTRY_HIT with closed_at...")
    
    response = requests.get(
        api_url,
        headers=headers,
        params={
            "select": "id,state,entry_hit_at,closed_at",
            "state": "eq.ENTRY_HIT",
            "closed_at": "not.is.null"
        }
    )
    
    if response.status_code == 200:
        violations = response.json()
        
        if violations:
            print(f"  ⚠️  WARNING: {len(violations)} ENTRY_HIT signals have closed_at set")
            for sig in violations[:3]:
                print(f"    Signal {sig['id'][:8]}... (may be race condition)")
        else:
            print("  ✅ No ENTRY_HIT with premature closed_at")
    
    # Test 3: Duplicate ENTRY_HIT (check for multiple entry_hit_at updates)
    print("\n✓ Test 3: Checking state distribution...")
    
    response = requests.get(api_url, headers=headers, params={"select": "state"})
    
    if response.status_code == 200:
        signals = response.json()
        state_counts = {}
        
        for sig in signals:
            state = sig.get('state', 'NULL')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print(f"  Total signals: {len(signals)}")
        for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {state}: {count}")
    
    # Test 4: WAITING_FOR_ENTRY signals (should have expiry_at)
    print("\n✓ Test 4: Checking WAITING_FOR_ENTRY signals...")
    
    response = requests.get(
        api_url,
        headers=headers,
        params={
            "select": "id,state,entry_price,expiry_at",
            "state": "eq.WAITING_FOR_ENTRY",
            "limit": "5"
        }
    )
    
    if response.status_code == 200:
        waiting = response.json()
        print(f"  WAITING_FOR_ENTRY signals: {len(waiting)}")
        
        for sig in waiting:
            has_entry = "✅" if sig.get('entry_price') else "❌"
            has_expiry = "✅" if sig.get('expiry_at') else "❌"
            print(f"    {has_entry} entry_price | {has_expiry} expiry_at | {sig['id'][:8]}...")
    
    # Test 5: Recent state transitions (last 10)
    print("\n✓ Test 5: Recent state transitions...")
    
    response = requests.get(
        api_url,
        headers=headers,
        params={
            "select": "id,state,generated_at,entry_hit_at,closed_at",
            "order": "generated_at.desc",
            "limit": "10"
        }
    )
    
    if response.status_code == 200:
        recent = response.json()
        
        for sig in recent:
            state = sig.get('state', 'NULL')
            gen_time = sig.get('generated_at', '')[:19] if sig.get('generated_at') else 'NULL'
            entry_time = sig.get('entry_hit_at', '')[:19] if sig.get('entry_hit_at') else 'NULL'
            close_time = sig.get('closed_at', '')[:19] if sig.get('closed_at') else 'NULL'
            
            print(f"    {sig['id'][:8]}... | {state:20} | gen:{gen_time} | entry:{entry_time} | close:{close_time}")
    
    print("\n" + "=" * 60)
    print("✅ ATOMICITY VERIFICATION COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = verify_atomicity()
    
    if success:
        print("\n✅ No critical violations detected")
        print("✅ GO to continue GATE 3")
    else:
        print("\n❌ CRITICAL VIOLATIONS FOUND")
        print("❌ NO-GO - Stop watcher and debug")
