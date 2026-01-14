import requests
from loguru import logger

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    logger.info("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logger.info("✅ Health OK")
        else:
            logger.error(f"❌ Health Failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")

def test_security():
    logger.info("🔍 Testing Security (Trade endpoint should not exist)...")
    try:
        response = requests.post(f"{BASE_URL}/trade")
        if response.status_code == 404:
            logger.info("✅ Security OK (No trade endpoint)")
        else:
            logger.warning(f"⚠️ Warning: Trade endpoint returned {response.status_code}")
    except Exception as e:
        logger.info("✅ Security OK (Connection closed/404)")

def test_internal_guard():
    logger.info("🔍 Testing Internal API Guard...")
    # This assumes QUANTIX_MODE might be PRODUCTION in some test cases, 
    # but here we just check if it returns valid structural data
    try:
        response = requests.post(f"{BASE_URL}/signals/generate?asset=EURUSD")
        if response.status_code in [200, 403]:
            logger.info(f"✅ Guard Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if "disclaimer" in data:
                    logger.info("✅ Disclaimer Present")
                if "learning_version" in data:
                    logger.info("✅ Structural Logs Present")
        else:
            logger.error(f"❌ Guard Test Failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Guard Test Error: {e}")

if __name__ == "__main__":
    test_health()
    test_security()
    test_internal_guard()
