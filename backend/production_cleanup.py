from quantix_core.database.connection import db
import os

def clear_db():
    cl = db.client
    print("--- Clearing Test Data from DB ---")
    
    # 1. Clear validation_events
    test_signals = ['health_check', '__health_check__', 'test_signal']
    res = cl.table("validation_events").delete().in_("signal_id", test_signals).execute()
    print(f"Deleted {len(res.data) if res.data else 0} test validation events.")

    # 2. Clear fx_analysis_log
    test_assets = ['SYSTEM_WATCHER', 'DEBUG_WATCHER', 'AUTO_ADJUSTER']
    res = cl.table("fx_analysis_log").delete().in_("asset", test_assets).execute()
    print(f"Deleted {len(res.data) if res.data else 0} test analysis logs.")
    
    # 3. Clear is_test=True signals
    res = cl.table("fx_signals").delete().eq("is_test", True).execute()
    print(f"Deleted {len(res.data) if res.data else 0} test signals.")

def delete_debris():
    debris = [
        "backend/check_all_watcher_logs.py",
        "backend/check_api_analysis_logs.py",
        "backend/check_signal_details.py",
        "backend/check_system_status.py",
        "backend/dump_logs.py",
        "backend/find_allowed_check_types.py",
        "backend/results.txt",
        "backend/status_output.txt",
        "backend/last_status.txt",
        "backend/find_allowed_states.py",
        "backend/force_signal_check.py",
        "backend/status_output.txt"
    ]
    
    # Also find all check_*.py and test_*.py debris
    root = "."
    for f in os.listdir(root):
        if f.startswith("check_") or f.startswith("test_") or f.startswith("debug_"):
            if f not in ["debug_signals_status.py"]: # Keep this one as it's useful
                debris.append(os.path.join(root, f))

    print("\n--- Deleting Local Debris ---")
    for d in set(debris):
        path = os.path.join(os.getcwd(), d)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted: {d}")
            except Exception as e:
                print(f"Failed to delete {d}: {e}")

if __name__ == "__main__":
    clear_db()
    delete_debris()
    print("\n✅ Cleanup Complete.")
