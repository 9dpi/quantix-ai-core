import asyncio
import json
import logging
import os
import sys

# Ensure backend path is configured
from quantix_core.config.settings import settings
from quantix_core.database.connection import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MT4_TEST")

async def test_mt4_endpoints():
    logger.info("Testing Phase 1 MT4 ID & Signals...")
    try:
        from fastapi.testclient import TestClient
        from quantix_core.api.main import app

        client = TestClient(app)

        # 1. Test Without Header
        res = client.get(f"{settings.API_PREFIX}/signals/pending")
        if res.status_code == 401:
            logger.info("✅ Security check passed: Unauthorized access blocked.")
        else:
            logger.error("❌ Security check failed.")

        # 2. Test With Header
        headers = {"Authorization": "Bearer DEMO_MT4_TOKEN_2026"}
        res = client.get(f"{settings.API_PREFIX}/signals/pending", headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            logger.info(f"✅ Polling successful. Received {data.get('count')} signals.")
            
            # Print payload schema
            if data.get('count') > 0:
                logger.info(f"Sample Payload: {json.dumps(data['signals'][0], indent=2)}")
            else:
                logger.warning("No ACTIVE signals in DB to show full payload schema, but API is working.")
        else:
            logger.error(f"❌ Polling failed. {res.status_code}: {res.text}")

        # 3. Test Callback
        callback_payload = {
            "signal_id": "test-uuid-123",
            "status": "EXECUTED_SUCCESS",
            "ticket": 445566,
            "error_code": 0,
            "error_message": "",
            "executed_price": 1.15555,
            "executed_lots": 0.12
        }
        res2 = client.post(f"{settings.API_PREFIX}/callback", headers=headers, json=callback_payload)
        if res2.status_code == 200:
             logger.info("✅ Callback POST successfully received format.")
        else:
             logger.error(f"❌ Callback POST failed. {res2.status_code}: {res2.text}")
             
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mt4_endpoints())
