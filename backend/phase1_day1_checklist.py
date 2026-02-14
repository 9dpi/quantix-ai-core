"""
Phase 1 - Day 1 Deployment Checklist
Quick verification before starting validation layer
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def check_database():
    """Check database connection"""
    try:
        from quantix_core.database.connection import SupabaseConnection
        db = SupabaseConnection()
        
        # Test query
        res = db.client.table("fx_signals").select("id").limit(1).execute()
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

def check_binance_api():
    """Check Binance API"""
    try:
        import requests
        r = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
        if r.status_code == 200:
            print("✅ Binance API: OK")
            return True
        else:
            print(f"❌ Binance API: FAILED - Status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Binance API: FAILED - {e}")
        return False

def check_validator_script():
    """Check validator script exists"""
    validator_path = Path(__file__).parent / "run_pepperstone_validator.py"
    if validator_path.exists():
        print("✅ Validator script: OK")
        return True
    else:
        print("❌ Validator script: NOT FOUND")
        return False

def check_log_directory():
    """Ensure log directory is writable"""
    try:
        log_file = Path(__file__).parent / "validation_audit.jsonl"
        log_file.touch(exist_ok=True)
        print("✅ Log directory: OK")
        return True
    except Exception as e:
        print(f"❌ Log directory: FAILED - {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 80)
    print("  PHASE 1 - DAY 1: PRE-FLIGHT CHECKLIST")
    print("=" * 80)
    print()
    
    checks = [
        ("Database Connection", check_database),
        ("Binance API", check_binance_api),
        ("Validator Script", check_validator_script),
        ("Log Directory", check_log_directory),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        print()
    
    print("=" * 80)
    if all(results):
        print("✅ ALL CHECKS PASSED - Ready to start validation layer")
        print()
        print("Next step:")
        print("  START_VALIDATION_LAYER.bat")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please fix issues before proceeding")
        return 1

if __name__ == "__main__":
    exit(main())
