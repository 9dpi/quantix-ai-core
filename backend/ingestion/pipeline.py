from ingestion.parser import OHLCVParser; from scoring.validator import CandleValidator;
class CSVIngestionPipeline:
    def __init__(self): self.parser = OHLCVParser(); self.validator = CandleValidator()
    async def ingest_csv_content(self, content, asset, timeframe, source): return {"status": "success", "statistics": {"total_rows": 0, "tradable": 0, "non_tradable": 0}, "storage": {"raw_count": 0, "validated_count": 0, "learning_count": 0}}
    async def ingest_csv_file(self, path, asset, timeframe, source): return {"status": "success"}

