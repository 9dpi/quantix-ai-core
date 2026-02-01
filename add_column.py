
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def add_telegram_column():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Supabase Python SDK doesn't support raw SQL easily unless you use RPC or another tool.
    # However, for a simple migration, we can assume the user has access to the SQL editor.
    # But as an agent, I should try to do it if possible.
    # Actually, I can use the 'run_command' with psql if I find where it is, 
    # but since psql failed earlier, I'll assume I can't run it directly.
    
    # Wait, I can use the postgrest API to check columns or use RPC if available.
    # Alternatively, I can just try to insert/update a record with that column and see if it fails.
    
    print("Please run this SQL in your Supabase SQL Editor:")
    print("ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS telegram_message_id BIGINT;")
    print("CREATE INDEX IF NOT EXISTS idx_fx_signals_telegram_id ON fx_signals(telegram_message_id);")

if __name__ == "__main__":
    add_telegram_column()
