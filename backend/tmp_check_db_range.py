import sys
import os
sys.path.append(os.path.join(os.getcwd()))

try:
    from quantix_core.database.connection import db
    from quantix_core.config.settings import settings
    
    res = db.client.table(settings.TABLE_SIGNALS).select("generated_at").order("generated_at", desc=False).limit(1).execute()
    if res.data:
        print(f"Oldest Signal: {res.data[0]['generated_at']}")
    else:
        print("No signals found in DB")
        
    res_count = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").execute()
    print(f"Total Signals: {res_count.count}")
    
except Exception as e:
    print(f"Error: {e}")
