"""
Quantix Explainability Engine
Gives the AI a voice to explain its probabilistic reasoning.
"""

from typing import Dict, Any, List
from schemas.signal import ExplainabilityTrace

class ExplainabilityEngine:
    """
    Constructs a narrative trace based on:
    1. Statistical Basis (Winrate, Expectancy)
    2. Structural Context (Session, Regime)
    3. Risk Assessment
    """

    def generate_trace(self, 
                       confidence: float, 
                       pattern_stats: Dict[str, Any], 
                       context: Dict[str, Any]) -> ExplainabilityTrace:
        
        # 1. Statistical Breakdown
        historical_winrate = pattern_stats.get('win_rate', 0.5)
        sample_size = pattern_stats.get('total_signals', 0)
        
        # 2. Derive Driving Factors
        factors = []
        if historical_winrate > 0.6:
            factors.append(f"Historical Winrate {historical_winrate*100:.1f}% > 60%")
        
        if context.get('session') in ['LONDON', 'LONDON_NY_OVERLAP']:
            factors.append("High Liquidity Session (London/NY)")
            
        if context.get('pattern') == 'PIN_BAR':
            factors.append("Strong Reversal Pattern Detected")
            
        # 3. Assess Risks
        risks = []
        if context.get('volatility') == 'LOW':
            risks.append("Low Volatility Environment")
            
        if sample_size < 50:
            risks.append(f"Low Sample Size ({sample_size} signals)")
            
        # 4. Synthesize Summary
        summary = "Standard setup"
        if confidence > 0.8:
            summary = "Prime Probability Setup with Confluence"
        elif confidence > 0.6:
            summary = "Valid Setup with moderate statistical backing"
        else:
            summary = "Low confidence speculative setup"
            
        return ExplainabilityTrace(
            summary=summary,
            driving_factors=factors,
            statistical_basis={
                "historical_winrate": historical_winrate,
                "sample_size": sample_size,
                "expectancy": pattern_stats.get('expectancy', 0.0)
            },
            risk_factors=risks
        )
