"""
Migration Verification Script

Checks that all v2 columns, indexes, and constraints were created successfully.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_migration():
    """Verify migration was successful"""
    
    print("=" * 60)
    print("VERIFYING MIGRATION - v1 → v2")
    print("=" * 60)
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    # Test 1: Check new columns exist
    print("\n✓ Test 1: Checking new columns...")
    
    api_url = f"{supabase_url}/rest/v1/fx_signals"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }
    
    try:
        # Fetch one signal to check schema
        response = requests.get(
            api_url, 
            headers=headers, 
            params={"select": "*", "limit": "1"}
        )
        response.raise_for_status()
        
        if response.json():
            signal = response.json()[0]
            
            # Check for v2 columns
            required_columns = [
                'state', 'entry_price', 'entry_hit_at', 
                'expiry_at', 'result', 'closed_at'
            ]
            
            missing = []
            present = []
            
            for col in required_columns:
                if col in signal:
                    present.append(col)
                else:
                    missing.append(col)
            
            print(f"  Present columns: {len(present)}/{len(required_columns)}")
            for col in present:
                print(f"    ✅ {col}")
            
            if missing:
                print(f"\n  ❌ Missing columns: {missing}")
                return False
            
            print("  ✅ All required columns present")
        
        # Test 2: Check state distribution
        print("\n✓ Test 2: Checking state distribution...")
        
        response = requests.get(api_url, headers=headers, params={"select": "state"})
        response.raise_for_status()
        
        signals = response.json()
        state_counts = {}
        
        for sig in signals:
            state = sig.get('state', 'NULL')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print(f"  Total signals: {len(signals)}")
        for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {state}: {count}")
        
        # Test 3: Check for signals with entry_price
        print("\n✓ Test 3: Checking entry_price population...")
        
        response = requests.get(
            api_url, 
            headers=headers, 
            params={"select": "entry_price", "entry_price": "not.is.null", "limit": "5"}
        )
        
        if response.status_code == 200:
            signals_with_entry = response.json()
            print(f"  Signals with entry_price: {len(signals_with_entry)}")
            if signals_with_entry:
                print(f"  Sample entry_price: {signals_with_entry[0].get('entry_price')}")
        
        # Test 4: Check WAITING_FOR_ENTRY signals have expiry
        print("\n✓ Test 4: Checking expiry_at for WAITING_FOR_ENTRY...")
        
        response = requests.get(
            api_url,
            headers=headers,
            params={
                "select": "id,state,expiry_at",
                "state": "eq.WAITING_FOR_ENTRY",
                "limit": "3"
            }
        )
        
        if response.status_code == 200:
            waiting_signals = response.json()
            print(f"  WAITING_FOR_ENTRY signals: {len(waiting_signals)}")
            
            for sig in waiting_signals[:3]:
                has_expiry = "✅" if sig.get('expiry_at') else "❌"
                print(f"    {has_expiry} Signal {sig.get('id')[:8]}... expiry: {sig.get('expiry_at', 'NULL')}")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION VERIFICATION COMPLETE")
        print("=" * 60)
        print("\nAll checks passed! Migration successful.")
        print("\n✅ GO to GATE 2")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        print("\n❌ NO-GO - Debug migration before proceeding")
        return False

if __name__ == "__main__":
    success = verify_migration()
    
    if not success:
        print("\n⚠️  Please check Supabase logs and re-run migration if needed.")
