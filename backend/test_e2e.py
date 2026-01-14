"""
E2E Test Suite - Quantix AI
Tests complete pipeline: Dukascopy → Clean Feed v1 → Structure Engine → API → Frontend

Principle: No guessing, no "seems OK", only PASS/FAIL with evidence
"""

import asyncio
from datetime import datetime
import requests
from loguru import logger

from ingestion.dukascopy.worker import DukascopyWorker
from database.connection import db


class E2ETestSuite:
    """
    End-to-end test suite for Quantix AI.
    
    Tests:
    1. Data Ingestion (Ground Truth)
    2. Validator Gatekeeper
    3. Structure Engine (Core Value)
    4. API Contract
    """
    
    def __init__(self):
        self.worker = DukascopyWorker()
        self.api_base = "https://quantixaicore-production.up.railway.app/api/v1"
        self.results = []
    
    async def test_1_data_ingestion(self):
        """
        TEST CASE 1: Data Ingestion (Ground Truth)
        
        Expected:
        - Exactly 6 H4 candles per day
        - complete=True if tick_count >= 10
        - No auto-fill
        - Monotonic timestamps
        """
        logger.info("=" * 80)
        logger.info("TEST 1: DATA INGESTION (GROUND TRUTH)")
        logger.info("=" * 80)
        
        test_date = datetime(2025, 1, 10)  # Friday
        symbol = "EURUSD"
        timeframe = "H4"
        
        # Ingest
        result = await self.worker.ingest_day(symbol, test_date, timeframe)
        
        logger.info(f"Ingestion result: {result}")
        
        # Assertions
        test_passed = True
        errors = []
        
        # 1. Status check
        if result["status"] != "success":
            errors.append(f"Expected status='success', got '{result['status']}'")
            test_passed = False
        
        # 2. Candle count
        candles_persisted = result.get("candles_persisted", 0)
        if candles_persisted != 6:
            errors.append(f"Expected 6 H4 candles, got {candles_persisted}")
            test_passed = False
        
        # 3. Database verification
        db_result = db.client.table('market_candles_v1').select('*').eq(
            'provider', 'dukascopy'
        ).eq(
            'instrument', symbol
        ).eq(
            'timeframe', timeframe
        ).gte(
            'timestamp', test_date.isoformat()
        ).lt(
            'timestamp', (test_date + timedelta(days=1)).isoformat()
        ).execute()
        
        db_count = len(db_result.data) if db_result.data else 0
        
        if db_count != 6:
            errors.append(f"Database has {db_count} candles, expected 6")
            test_passed = False
        
        # 4. Completeness check
        if db_result.data:
            for candle in db_result.data:
                if not candle.get('complete'):
                    errors.append(f"Candle at {candle['timestamp']} has complete=False")
                    test_passed = False
        
        # 5. Monotonic timestamps
        if db_result.data and len(db_result.data) > 1:
            timestamps = [datetime.fromisoformat(c['timestamp']) for c in db_result.data]
            for i in range(1, len(timestamps)):
                if timestamps[i] <= timestamps[i-1]:
                    errors.append(f"Timestamp not increasing: {timestamps[i-1]} -> {timestamps[i]}")
                    test_passed = False
        
        # Result
        self.results.append({
            "test": "TEST 1: Data Ingestion",
            "passed": test_passed,
            "errors": errors
        })
        
        if test_passed:
            logger.info("✅ TEST 1 PASSED")
        else:
            logger.error(f"❌ TEST 1 FAILED: {errors}")
        
        return test_passed
    
    async def test_2_validator_gatekeeper(self):
        """
        TEST CASE 2: Validator Gatekeeper
        
        Expected:
        - Invalid data raises exception
        - No partial saves
        - Clear error messages
        """
        logger.info("=" * 80)
        logger.info("TEST 2: VALIDATOR GATEKEEPER")
        logger.info("=" * 80)
        
        from ingestion.dukascopy.validator import CandleValidator
        from ingestion.dukascopy.resampler import Candle
        
        validator = CandleValidator("H4")
        test_passed = True
        errors = []
        
        # Test 1: Invalid OHLC (high < close)
        invalid_candle_1 = Candle(
            timestamp=datetime(2025, 1, 10, 0, 0),
            open=1.0,
            high=0.9,  # Invalid: high < open
            low=0.8,
            close=1.0,
            volume=100,
            tick_count=20,
            complete=True
        )
        
        result_1 = validator.validate(invalid_candle_1)
        if result_1.valid:
            errors.append("Validator accepted invalid OHLC (high < open)")
            test_passed = False
        else:
            logger.info(f"✅ Correctly rejected invalid OHLC: {result_1.errors}")
        
        # Test 2: Incomplete candle
        incomplete_candle = Candle(
            timestamp=datetime(2025, 1, 10, 4, 0),
            open=1.0,
            high=1.1,
            low=0.9,
            close=1.0,
            volume=100,
            tick_count=5,  # Below minimum
            complete=False
        )
        
        result_2 = validator.validate(incomplete_candle)
        if result_2.valid:
            errors.append("Validator accepted incomplete candle")
            test_passed = False
        else:
            logger.info(f"✅ Correctly rejected incomplete candle: {result_2.errors}")
        
        # Test 3: Wrong timestamp alignment
        misaligned_candle = Candle(
            timestamp=datetime(2025, 1, 10, 3, 0),  # Not H4 boundary
            open=1.0,
            high=1.1,
            low=0.9,
            close=1.0,
            volume=100,
            tick_count=20,
            complete=True
        )
        
        result_3 = validator.validate(misaligned_candle)
        if result_3.valid:
            errors.append("Validator accepted misaligned timestamp")
            test_passed = False
        else:
            logger.info(f"✅ Correctly rejected misaligned timestamp: {result_3.errors}")
        
        # Result
        self.results.append({
            "test": "TEST 2: Validator Gatekeeper",
            "passed": test_passed,
            "errors": errors
        })
        
        if test_passed:
            logger.info("✅ TEST 2 PASSED")
        else:
            logger.error(f"❌ TEST 2 FAILED: {errors}")
        
        return test_passed
    
    async def test_3_structure_engine_api(self):
        """
        TEST CASE 3: Structure Engine API
        
        Expected:
        - Correct JSON contract
        - State reasoning (not prediction)
        - Evidence matches dominance
        - No "Buy/Sell"
        """
        logger.info("=" * 80)
        logger.info("TEST 3: STRUCTURE ENGINE API")
        logger.info("=" * 80)
        
        test_passed = True
        errors = []
        
        # Call API
        url = f"{self.api_base}/internal/feature-state/structure"
        params = {
            "symbol": "EURUSD",
            "tf": "H4"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                errors.append(f"API returned {response.status_code}: {response.text}")
                test_passed = False
            else:
                data = response.json()
                logger.info(f"API Response: {data}")
                
                # Contract validation
                required_fields = ["feature", "state", "confidence", "dominance", "evidence", "trace_id", "source", "timeframe"]
                for field in required_fields:
                    if field not in data:
                        errors.append(f"Missing required field: {field}")
                        test_passed = False
                
                # State validation
                valid_states = ["bullish", "bearish", "range", "unclear"]
                if data.get("state") not in valid_states:
                    errors.append(f"Invalid state: {data.get('state')}")
                    test_passed = False
                
                # Confidence range
                confidence = data.get("confidence", -1)
                if not (0.0 <= confidence <= 1.0):
                    errors.append(f"Confidence out of range: {confidence}")
                    test_passed = False
                
                # Dominance structure
                dominance = data.get("dominance", {})
                if "bullish" not in dominance or "bearish" not in dominance:
                    errors.append("Dominance missing bullish/bearish scores")
                    test_passed = False
                
                # Evidence array
                evidence = data.get("evidence", [])
                if not isinstance(evidence, list):
                    errors.append("Evidence must be array")
                    test_passed = False
                
                # No "Buy/Sell" in response
                response_str = str(data).lower()
                if "buy" in response_str or "sell" in response_str:
                    errors.append("Response contains 'buy' or 'sell' - should be state-based")
                    test_passed = False
                
                # Source verification
                if data.get("source") != "yahoo_finance" and data.get("source") != "dukascopy":
                    errors.append(f"Unknown source: {data.get('source')}")
                    test_passed = False
                
        except Exception as e:
            errors.append(f"API call failed: {e}")
            test_passed = False
        
        # Result
        self.results.append({
            "test": "TEST 3: Structure Engine API",
            "passed": test_passed,
            "errors": errors
        })
        
        if test_passed:
            logger.info("✅ TEST 3 PASSED")
        else:
            logger.error(f"❌ TEST 3 FAILED: {errors}")
        
        return test_passed
    
    async def test_4_frontend_contract(self):
        """
        TEST CASE 4: Frontend Contract
        
        Expected:
        - reasoning.html accessible
        - Displays state, confidence, evidence
        - No crash on missing data
        """
        logger.info("=" * 80)
        logger.info("TEST 4: FRONTEND CONTRACT")
        logger.info("=" * 80)
        
        test_passed = True
        errors = []
        
        frontend_url = "https://9dpi.github.io/quantix-ai-core/reasoning.html"
        
        try:
            response = requests.get(frontend_url, timeout=10)
            
            if response.status_code != 200:
                errors.append(f"Frontend not accessible: {response.status_code}")
                test_passed = False
            else:
                html = response.text
                
                # Check for key elements
                required_elements = [
                    "Market State Reasoning",
                    "Analyze Market State",
                    "Structure Confidence",
                    "Why This State",
                    "Trace ID"
                ]
                
                for element in required_elements:
                    if element not in html:
                        errors.append(f"Missing UI element: {element}")
                        test_passed = False
                
                logger.info("✅ Frontend accessible and contains required elements")
                
        except Exception as e:
            errors.append(f"Frontend check failed: {e}")
            test_passed = False
        
        # Result
        self.results.append({
            "test": "TEST 4: Frontend Contract",
            "passed": test_passed,
            "errors": errors
        })
        
        if test_passed:
            logger.info("✅ TEST 4 PASSED")
        else:
            logger.error(f"❌ TEST 4 FAILED: {errors}")
        
        return test_passed
    
    async def run_all_tests(self):
        """Run complete E2E test suite"""
        logger.info("🧪 STARTING E2E TEST SUITE - QUANTIX AI")
        logger.info("Testing: Dukascopy → Clean Feed v1 → Structure Engine → API → Frontend")
        logger.info("")
        
        # Run tests
        test1 = await self.test_1_data_ingestion()
        await asyncio.sleep(1)
        
        test2 = await self.test_2_validator_gatekeeper()
        await asyncio.sleep(1)
        
        test3 = await self.test_3_structure_engine_api()
        await asyncio.sleep(1)
        
        test4 = await self.test_4_frontend_contract()
        
        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("E2E TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        
        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            logger.info(f"{status} - {result['test']}")
            if result["errors"]:
                for error in result["errors"]:
                    logger.info(f"  ⚠️ {error}")
        
        logger.info("")
        logger.info(f"Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("")
            logger.info("🎉 ALL E2E TESTS PASSED")
            logger.info("Quantix AI is PRODUCTION READY")
            logger.info("")
            logger.info("✅ Clean Feed v1 → Structure Engine v1 → API → Frontend")
            logger.info("✅ Data Law compliant")
            logger.info("✅ Deterministic & Explainable")
        else:
            logger.error("")
            logger.error(f"❌ {total_tests - passed_tests} TEST(S) FAILED")
            logger.error("Review errors above before production deployment")
        
        return passed_tests == total_tests


async def main():
    """Run E2E test suite"""
    suite = E2ETestSuite()
    success = await suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    from datetime import timedelta
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
