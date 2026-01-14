from loguru import logger

class CandleValidator:
    def batch_validate(self, candles):
        """
        Validate candles - accepts volume = 0 for Forex data
        Returns validation statistics
        """
        if not candles:
            return {
                "results": [],
                "tradable": 0,
                "total": 0,
                "non_tradable": 0,
                "avg_learning_weight": 0.0,
                "breakdown": {}
            }
        
        total = len(candles)
        tradable = 0
        non_tradable = 0
        weights = []
        
        for candle in candles:
            # Basic validation: must have OHLC
            try:
                open_price = float(candle.get('open', 0))
                high = float(candle.get('high', 0))
                low = float(candle.get('low', 0))
                close = float(candle.get('close', 0))
                
                # Volume can be 0 for Forex (OTC market)
                volume = float(candle.get('volume', 0))
                
                # Validate OHLC logic
                if high >= max(open_price, close) and low <= min(open_price, close):
                    if high > 0 and low > 0:  # Prices must be positive
                        tradable += 1
                        # Calculate learning weight based on volatility
                        volatility = (high - low) / ((high + low) / 2) if (high + low) > 0 else 0
                        weight = min(1.0, volatility * 100)  # Normalize to 0-1
                        weights.append(weight)
                    else:
                        non_tradable += 1
                else:
                    non_tradable += 1
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid candle data: {e}")
                non_tradable += 1
        
        avg_weight = sum(weights) / len(weights) if weights else 0.0
        
        logger.info(f"✅ Validated: {tradable}/{total} tradable (volume=0 accepted)")
        
        return {
            "results": [],
            "tradable": tradable,
            "total": total,
            "non_tradable": non_tradable,
            "avg_learning_weight": avg_weight,
            "breakdown": {"NORMAL": tradable, "INVALID": non_tradable}
        }

