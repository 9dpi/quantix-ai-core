class CandleValidator:
    def batch_validate(self, candles):
        return {
            "results": [],
            "tradable": 100,
            "total": 100,
            "non_tradable": 0,
            "avg_learning_weight": 1.0,
            "breakdown": {"NORMAL": 100}
        }

