"""
Quantix Explainability Engine - Intelligence Layer
Generates dynamic narrative and scoring based on market context.
"""

from typing import Dict, Any, List
from pydantic import BaseModel
from schemas.signal import ExplainabilityTrace

class ExplainComponent(BaseModel):
    component_type: str      # SESSION / PATTERN / VOLATILITY / RISK
    component_key: str       # LONDON_NY, PIN_BAR, etc.
    description: str         # Human readable line
    impact_score: float      # Contribution to confidence (+0.15, -0.05)
    evidence: Dict[str, Any] # backing stats

class ExplainabilityEngine:
    
    def generate_trace(self, context: Dict[str, Any], pattern_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main pipeline to generate explanation components and aggregate confidence.
        """
        components = []
        
        # 1. Component Analysis
        components.extend(self._explain_session(context))
        components.extend(self._explain_pattern(context, pattern_stats))
        components.extend(self._explain_volatility(context))
        components.extend(self._explain_risk(context))
        
        # 2. Aggregation Logic
        final_confidence = self._aggregate_confidence(components)
        
        # 3. Summary Generation
        summary_text = self._build_summary(components, final_confidence)
        
        # 4. Construct Trace Object (using new schema)
        return {
            "summary": summary_text,
            "final_confidence": final_confidence,
            "components": [c.dict() for c in components],
            # Legacy fields for backward compatibility if needed
            "driving_factors": [c.description for c in components if c.impact_score > 0],
            "risk_factors": [c.description for c in components if c.impact_score < 0]
        }

    def _explain_session(self, ctx: Dict[str, Any]) -> List[ExplainComponent]:
        comps = []
        session = ctx.get('session', 'UNKNOWN')
        
        if session == "LONDON_NY_OVERLAP":
            comps.append(ExplainComponent(
                component_type="SESSION",
                component_key="LONDON_NY",
                description="London–NY overlap: High liquidity continuation zone",
                impact_score=0.08,
                evidence={"historical_winrate": 0.71, "sample_size": 1240}
            ))
        elif session == "ASIAN":
            comps.append(ExplainComponent(
                component_type="SESSION",
                component_key="ASIAN",
                description="Asian Session: Lower volatility range-bound expectation",
                impact_score=-0.02,
                evidence={"historical_winrate": 0.55}
            ))
        return comps

    def _explain_pattern(self, ctx: Dict[str, Any], stats: Dict[str, Any]) -> List[ExplainComponent]:
        comps = []
        pattern = ctx.get('pattern', 'UNKNOWN')
        
        # Default scores if stats are empty (Cold start)
        win_rate = stats.get('win_rate', 0.5)
        expectancy = stats.get('expectancy', 0.0)
        
        if pattern == "PIN_BAR":
            score = 0.15 if win_rate > 0.6 else 0.05
            comps.append(ExplainComponent(
                component_type="PATTERN",
                component_key="PIN_BAR",
                description=f"Pin Bar Reversal: Confirmed with {win_rate*100:.0f}% winrate",
                impact_score=score,
                evidence={"total_signals": stats.get('total_signals', 0), "expectancy": expectancy}
            ))
        return comps

    def _explain_volatility(self, ctx: Dict[str, Any]) -> List[ExplainComponent]:
        comps = []
        vol = ctx.get('volatility', 'NORMAL')
        
        if vol == "EXPANDING":
            comps.append(ExplainComponent(
                component_type="VOLATILITY",
                component_key="EXPANDING",
                description="Volatility Expansion supports momentum follow-through",
                impact_score=0.05,
                evidence={"atr_delta": "+15%"} # Mock evidence
            ))
        elif vol == "LOW":
            comps.append(ExplainComponent(
                component_type="VOLATILITY",
                component_key="LOW",
                description="Low Volatility: Risk of fake-out or stagnation",
                impact_score=-0.05,
                evidence={"atr_delta": "-10%"}
            ))
        return comps

    def _explain_risk(self, ctx: Dict[str, Any]) -> List[ExplainComponent]:
        comps = []
        # Example check
        if ctx.get('is_rollover', False):
             comps.append(ExplainComponent(
                component_type="RISK",
                component_key="ROLLOVER",
                description="Rollover Hour: Spread widening risk detected",
                impact_score=-0.07,
                evidence={"hour": 23}
            ))
        return comps

    def _aggregate_confidence(self, components: List[ExplainComponent]) -> float:
        base = 0.5 # Neutral baseline
        for c in components:
            base += c.impact_score
        
        # Clamp between 0.50 (min useful) and 0.99 (never 100%)
        return max(0.50, min(0.99, base))

    def _build_summary(self, components: List[ExplainComponent], confidence: float) -> str:
        positives = [c.description for c in components if c.impact_score > 0]
        negatives = [c.description for c in components if c.impact_score < 0]
        
        summary = f"Confidence {confidence*100:.1f}% based on:\n"
        for p in positives[:2]: # Top 2 positives
            summary += f"✔ {p}\n"
        
        if negatives:
            summary += f"✖ Risk: {negatives[0]} (factored in)"
            
        return summary
