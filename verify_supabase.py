import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env from backend/.env
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv('backend/.env')

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def verify_connection():
    print(f"Connecting to Supabase: {url}")
    if not url or not key:
        print("❌ Missing Supabase Credentials")
        return

    try:
        supabase: Client = create_client(url, key)
        # Try a simple fetch (e.g., system time or empty select)
        # We'll just check if client initializes and maybe list tables logic via a simple query
        
        # Check signals table existence
        print("Querying 'fx_signals' table...")
        res = supabase.table("fx_signals").select("id").limit(1).execute()
        print(f"✅ Connection Success! Data: {res.data}")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_connection()
