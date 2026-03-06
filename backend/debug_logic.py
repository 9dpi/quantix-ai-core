import sys
sys.stdout.reconfigure(encoding='utf-8')
from quantix_core.database.connection import db

res = db.client.table('fx_analysis_log').select('timestamp,status').eq('asset', 'ANALYZER_LOG').order('timestamp', desc=True).limit(50).execute()

with open('debug_output3.txt', 'w', encoding='utf-8') as f:
    for r in res.data:
        st = str(r['status'])
        if 'evaluat' in st.lower() or 'reject' in st.lower() or 'fail' in st.lower() or 'score' in st.lower():
            f.write(f"[{r['timestamp'][:19]}] {st}\n")
