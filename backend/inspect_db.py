"""
Database Inspection Script
Check if Quantix has data to learn from
"""

import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('backend/.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def inspect_database():
    """Check database for learning-ready data."""
    
    print("=" * 70)
    print("QUANTIX AI CORE - DATABASE INSPECTION")
    print("=" * 70)
    print()
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check 1: Raw candles table
    print("📊 Checking: raw_candles")
    print("-" * 70)
    try:
        result = supabase.table('raw_candles').select('*', count='exact').limit(5).execute()
        total_candles = result.count if hasattr(result, 'count') else len(result.data)
        print(f"✅ Total raw candles: {total_candles:,}")
        
        if result.data:
            print(f"   Sample (first 5):")
            for i, candle in enumerate(result.data[:5], 1):
                print(f"   {i}. {candle.get('asset', 'N/A')} @ {candle.get('time', 'N/A')}")
        else:
            print("   ⚠️  No data found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check 2: Validated candles (learning set)
    print("🧠 Checking: validated_candles (Learning Set)")
    print("-" * 70)
    try:
        result = supabase.table('validated_candles').select('*', count='exact').limit(5).execute()
        total_validated = result.count if hasattr(result, 'count') else len(result.data)
        print(f"✅ Total validated candles: {total_validated:,}")
        
        if result.data:
            print(f"   Sample (first 5):")
            for i, candle in enumerate(result.data[:5], 1):
                lw = candle.get('learning_weight', 0)
                print(f"   {i}. {candle.get('asset', 'N/A')} - Weight: {lw:.2f}")
        else:
            print("   ⚠️  No validated data for learning")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check 3: Ingestion audit log
    print("📝 Checking: ingestion_audit_log")
    print("-" * 70)
    try:
        result = supabase.table('ingestion_audit_log').select('*').order('ingested_at', desc=True).limit(10).execute()
        print(f"✅ Total ingestion records: {len(result.data)}")
        
        if result.data:
            print(f"   Recent ingestions:")
            for i, log in enumerate(result.data[:5], 1):
                print(f"   {i}. {log.get('asset', 'N/A')} - {log.get('total_rows', 0)} rows - {log.get('status', 'N/A')}")
        else:
            print("   ⚠️  No ingestion history")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check 4: New learning tables (v3.2)
    print("🆕 Checking: New Learning Tables (v3.2)")
    print("-" * 70)
    
    # Check market_candles_clean
    try:
        result = supabase.table('market_candles_clean').select('*', count='exact').limit(1).execute()
        print(f"   market_candles_clean: {result.count if hasattr(result, 'count') else 'Table exists'}")
    except Exception as e:
        print(f"   market_candles_clean: ❌ Not created yet ({str(e)[:50]}...)")
    
    # Check signal_outcomes
    try:
        result = supabase.table('signal_outcomes').select('*', count='exact').limit(1).execute()
        print(f"   signal_outcomes: {result.count if hasattr(result, 'count') else 'Table exists'}")
    except Exception as e:
        print(f"   signal_outcomes: ❌ Not created yet ({str(e)[:50]}...)")
    
    # Check learning_memory
    try:
        result = supabase.table('learning_memory').select('*', count='exact').limit(1).execute()
        print(f"   learning_memory: {result.count if hasattr(result, 'count') else 'Table exists'}")
    except Exception as e:
        print(f"   learning_memory: ❌ Not created yet ({str(e)[:50]}...)")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Calculate learning readiness
    try:
        validated_result = supabase.table('validated_candles').select('*', count='exact').limit(1).execute()
        validated_count = validated_result.count if hasattr(validated_result, 'count') else 0
        
        if validated_count > 0:
            print(f"✅ Quantix HAS data to learn from: {validated_count:,} validated candles")
            print(f"   These candles have learning_weight > 0")
            print(f"   Ready for pattern analysis and signal generation")
        else:
            print(f"⚠️  Quantix does NOT have learning data yet")
            print(f"   Next steps:")
            print(f"   1. Upload CSV data via Ingestion Portal")
            print(f"   2. Data will be validated and stored in validated_candles")
            print(f"   3. Quantix can then learn from this data")
    except Exception as e:
        print(f"⚠️  Could not determine learning readiness: {e}")
    
    print()
    
    # Check if v3.2 schema is deployed
    try:
        supabase.table('learning_memory').select('*').limit(1).execute()
        print("✅ v3.2 Learning Schema: DEPLOYED")
    except:
        print("⚠️  v3.2 Learning Schema: NOT DEPLOYED YET")
        print("   Run: supabase/006_continuous_learning_schema.sql")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(inspect_database())
