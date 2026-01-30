"""
Simple Manual Backup Script - Export fx_signals table

Uses direct HTTP requests to Supabase REST API.
No dependencies needed except requests.
"""

import os
import json
import requests
from datetime import datetime

def create_backup():
    """Export fx_signals table to JSON backup file"""
    
    print("=" * 60)
    print("CREATING MANUAL BACKUP - fx_signals table")
    print("=" * 60)
    
    # Get credentials from environment
    # Try service role key first (has full access), fallback to anon key
    supabase_url = os.getenv("SUPABASE_URL", "YOUR_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
    
    if "YOUR_SUPABASE" in supabase_url or "YOUR_SUPABASE" in supabase_key:
        print("\n❌ ERROR: Please set SUPABASE_URL and SUPABASE_KEY")
        print("\nOption 1: Set in .env file")
        print("Option 2: Edit this script and replace YOUR_SUPABASE_URL and YOUR_SUPABASE_KEY")
        return False
    
    # Fetch all signals via REST API
    api_url = f"{supabase_url}/rest/v1/fx_signals"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }
    
    print(f"\nFetching data from: {api_url}")
    
    try:
        response = requests.get(api_url, headers=headers, params={"select": "*"})
        response.raise_for_status()
        
        signals = response.json()
        print(f"✅ Retrieved {len(signals)} signals")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_fx_signals_{timestamp}.json"
        
        # Save to file
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "table": "fx_signals",
            "record_count": len(signals),
            "supabase_url": supabase_url,
            "data": signals
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"\n✅ Backup saved to: {backup_file}")
        print(f"Records backed up: {len(signals)}")
        
        # Show sample
        if signals:
            print("\nSample record (first signal):")
            sample = signals[0]
            for key in ['id', 'asset', 'direction', 'status', 'generated_at']:
                if key in sample:
                    print(f"  {key}: {sample[key]}")
        
        print("\n" + "=" * 60)
        print("✅ BACKUP COMPLETE")
        print("=" * 60)
        print(f"Backup file: {backup_file}")
        print(f"Records: {len(signals)}")
        print("\n⚠️  Keep this file safe for rollback if needed!")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Backup failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_backup()
    
    if success:
        print("\n✅ Backup created successfully!")
        print("You can now proceed with migration.")
    else:
        print("\n❌ Backup failed!")
        print("Do NOT proceed with migration until backup is successful.")
