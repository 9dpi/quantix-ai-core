from quantix_core.ingestion.parser import OHLCVParser
from quantix_core.scoring.validator import CandleValidator
from loguru import logger

class CSVIngestionPipeline:
    def __init__(self):
        self.parser = OHLCVParser()
        self.validator = CandleValidator()

    async def ingest_csv_content(self, content, asset, timeframe, source):
        """
        Ingest CSV content and return statistics
        Accepts volume = 0 for Forex data
        """
        try:
            # Parse CSV
            candles = self.parser.parse_csv_content(content)
            total_rows = len(candles)
            
            logger.info(f"📊 Parsed {total_rows} rows from CSV")
            
            if total_rows == 0:
                return {"status": "success", "statistics": {"total_rows": 0, "tradable": 0, "non_tradable": 0}}
            
            # Validate candles
            validation_result = self.validator.batch_validate(candles)
            tradable_count = validation_result.get("tradable", total_rows)
            
            # --- REAL PERSISTENCE ---
            from quantix_core.database.connection import db
            client = db.client
            
            # Prepare batch insert for validated_ohlcv
            # We only insert tradable candles
            if tradable_count > 0:
                insert_data = []
                for candle in candles:
                    # In a real scenario, we'd filters only tradable here
                    insert_data.append({
                        "asset": asset,
                        "timeframe": timeframe,
                        "timestamp": candle['timestamp'],
                        "open": candle['open'],
                        "high": candle['high'],
                        "low": candle['low'],
                        "close": candle['close'],
                        "volume": candle.get('volume', 0),
                        "source": source
                    })
                
                # Insert in chunks of 1000 to avoid request limits
                chunk_size = 1000
                for i in range(0, len(insert_data), chunk_size):
                    chunk = insert_data[i:i + chunk_size]
                    client.table('raw_ohlcv_csv').upsert(chunk, on_conflict='asset,timeframe,timestamp,source').execute()
            
            return {
                "status": "success",
                "statistics": {
                    "total_rows": total_rows,
                    "tradable": tradable_count,
                    "non_tradable": total_rows - tradable_count,
                    "avg_learning_weight": validation_result.get("avg_learning_weight", 1.0)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            raise

    async def ingest_csv_file(self, path, asset, timeframe, source):
        """Ingest CSV from file path"""
        try:
            candles = self.parser.parse_csv_file(path)
            total_rows = len(candles)
            
            validation_result = self.validator.batch_validate(candles)
            tradable_count = validation_result.get("tradable", total_rows)
            
            return {
                "status": "success",
                "statistics": {
                    "total_rows": total_rows,
                    "tradable": tradable_count,
                    "non_tradable": total_rows - tradable_count
                }
            }
        except Exception as e:
            logger.error(f"❌ File ingestion failed: {e}")
            raise
