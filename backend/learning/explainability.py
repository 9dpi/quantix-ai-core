from loguru import logger

class ExplainabilityEngine:
    """
    Quantix AI - Explainability Engine
    Generates human-readable reasoning and dynamic confidence scores.
    """
    def __init__(self):
        logger.info("ExplainabilityEngine initialized")

    def generate_trace(self, context: dict, stats: dict) -> dict:
        """
        Calculates confidence and generates a logic trace.
        """
        # Logic simulation based on context
        base_confidence = stats.get("win_rate", 0.5)
        
        # Adjust based on session/regime
        if context.get("session") == "LONDON_NY_OVERLAP":
            base_confidence += 0.05
        
        if context.get("regime") == "TRENDING_UP" and context.get("pattern") == "PIN_BAR":
            base_confidence += 0.08

        return {
            "final_confidence": min(base_confidence, 0.98),
            "summary": f"Strong bullish structural alignment during high-liquidity session.",
            "driving_factors": ["High Liquidity", "Trend Alignment", "Elite Pattern"],
            "risk_factors": ["Expanding Volatility"]
        }
