from ingestion.parser import OHLCVParser
from scoring.validator import CandleValidator
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
                return {
                    "status": "success",
                    "statistics": {
                        "total_rows": 0,
                        "tradable": 0,
                        "non_tradable": 0
                    },
                    "storage": {
                        "raw_count": 0,
                        "validated_count": 0,
                        "learning_count": 0
                    }
                }
            
            # Validate candles (accept volume = 0)
            validation_result = self.validator.batch_validate(candles)
            
            tradable_count = validation_result.get("tradable", total_rows)
            non_tradable_count = validation_result.get("non_tradable", 0)
            avg_weight = validation_result.get("avg_learning_weight", 1.0)
            
            logger.info(f"✅ Validation: {tradable_count}/{total_rows} tradable")
            
            return {
                "status": "success",
                "statistics": {
                    "total_rows": total_rows,
                    "tradable": tradable_count,
                    "non_tradable": non_tradable_count,
                    "avg_learning_weight": avg_weight
                },
                "storage": {
                    "raw_count": total_rows,
                    "validated_count": tradable_count,
                    "learning_count": tradable_count
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
