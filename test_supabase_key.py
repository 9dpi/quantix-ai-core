from supabase import create_client

# Thay bằng key thật từ Supabase
SUPABASE_URL = "https://gvglzvjsexeaectypkyk.supabase.co"
SUPABASE_KEY = "eyJ..."  # Dán key publishable vào đây

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("fx_signals").select("id").limit(1).execute()
    print("✅ Key hợp lệ! Kết nối thành công.")
except Exception as e:
    print(f"❌ Lỗi: {e}")
