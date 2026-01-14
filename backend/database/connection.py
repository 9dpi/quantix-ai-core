"""
Supabase database connection and client management
"""
from supabase import create_client, Client
from config.settings import settings
from loguru import logger
from typing import Optional, List, Dict, Any, Union
import asyncio
from contextlib import asynccontextmanager

class SupabaseConnection:
    _instance: Optional["SupabaseConnection"] = None
    _client: Optional[Client] = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if self._client is None: self._initialize_client()
    def _initialize_client(self):
        try:
            self._client = create_client(supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_KEY)
            logger.info(" Supabase client initialized")
        except Exception as e: logger.error(f" Failed to initialize: {e}"); raise
    @property
    def client(self) -> Client:
        if self._client is None: self._initialize_client()
        return self._client
    async def health_check(self) -> bool:
        try: result = self._client.table(settings.TABLE_SIGNALS).select("id").limit(1).execute(); return True
        except Exception: return False
    async def execute(self, query: str, *args): pass
    async def fetch(self, query: str, *args): return []
    async def executemany(self, query: str, data_list: List[tuple]): pass
    @asynccontextmanager
    async def transaction(self): yield self

db = SupabaseConnection()
def get_db() -> Client: return db.client

