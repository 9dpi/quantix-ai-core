import sys
import os
sys.path.append(os.getcwd())

print("STARTING TEST")
try:
    from quantix_core.database.connection import db, SupabaseConnection
    print(f"Imported db: {db}")
    print(f"Imported Class: {SupabaseConnection}")
    
    conn = SupabaseConnection()
    print(f"New Instance: {conn}")
    
except Exception as e:
    print(f"Error: {e}")
