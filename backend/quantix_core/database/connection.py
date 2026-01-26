"""
Supabase database connection and client management
"""
from supabase import create_client, Client
from quantix_core.config.settings import settings
from loguru import logger
from typing import Optional, List, Dict, Any, Union
import asyncio
from contextlib import asynccontextmanager

class SupabaseConnection:
    _instance: Optional["SupabaseConnection"] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("⚠️ SUPABASE_URL or SUPABASE_KEY is missing!")
                return
                
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            # Do not raise - allow app to start so we can debug via API
            self._client = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._initialize_client()
        return self._client

    async def health_check(self) -> bool:
        try:
            # Try to query the signals table as a heartbeat
            self._client.table(settings.TABLE_SIGNALS).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            return False

    async def execute(self, query: str, *args):
        # shim for simple INSERT in csv_ingestion router
        if "INSERT INTO ingestion_audit_log" in query:
             data = {
                 "asset": args[0], "timeframe": args[1], "source": args[2],
                 "total_rows": args[3], "tradable_count": args[4],
                 "non_tradable_count": args[5], "avg_learning_weight": float(args[6]),
                 "status": args[7]
             }
             return self.client.table('ingestion_audit_log').insert(data).execute()
        return None

    async def fetch(self, query: str, *args):
        try:
            if not self.client:
                return []

            # 1. Shim for signals
            if "FROM fx_signals" in query:
                q = self.client.table('fx_signals').select('*')
                if "ORDER BY generated_at DESC" in query:
                    q = q.order('generated_at', desc=True)
                if "LIMIT" in query:
                    try:
                        limit_part = query.split("LIMIT")[-1].strip()
                        limit = int(limit_part)
                        q = q.limit(limit)
                    except:
                        q = q.limit(5)
                if "WHERE status = 'ACTIVE'" in query:
                    q = q.eq("status", "ACTIVE")
                    
                res = q.execute()
                return res.data if res.data else []

            # 2. Shim for global stats 
            if "SELECT SUM(tradable_count)" in query:
                res = self.client.table('ingestion_audit_log').select('tradable_count,total_rows,avg_learning_weight').execute()
                if not res.data: return []
                import pandas as pd
                df = pd.DataFrame(res.data)
                return [{
                    "total_learning": int(df['tradable_count'].sum()),
                    "total_ingested": int(df['total_rows'].sum()),
                    "avg_weight": float(df['avg_learning_weight'].mean())
                }]
            
            return []
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return []

db = SupabaseConnection()

def get_db() -> Client:
    return db.client

