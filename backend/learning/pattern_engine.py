"""
Quantix Pattern Engine - Memory & Bayesian Learning
"""

import hashlib
import json
from typing import Dict, Any, Optional
from loguru import logger
from database.connection import db

class PatternEngine:
    """Handles pattern hashing, statistical memory, and confidence adjustment"""
    
    LEARNING_RATE = 0.05 # alpha
    MIN_DATA_POINTS = 30 # For statistical significance

    def generate_hash(self, context: Dict[str, Any]) -> str:
        """Create a unique SHA256 hash for a given market context"""
        # Sort keys to ensure deterministic hashing
        canonical_context = json.dumps(context, sort_keys=True)
        return hashlib.sha256(canonical_context.encode()).hexdigest()

    async def generate_confidence(self, pattern_hash: str) -> float:
        """
        Bayesian Confidence Generation:
        Prior (0.55) -> Likelihood (Win Rate) -> Expectancy Boost
        """
        try:
            # Fetch pattern stats from Supabase
            query = "SELECT total_signals, win_count, expectancy FROM pattern_stats WHERE pattern_hash = $1"
            stats = await db.fetch(query, pattern_hash)
            
            if not stats or stats[0]['total_signals'] < self.MIN_DATA_POINTS:
                return 0.55 # Base confidence for new patterns
            
            s = stats[0]
            win_rate = s['win_count'] / s['total_signals']
            expectancy = float(s['expectancy'])
            
            # Clamp expectancy boost to +/- 0.2
            boost = max(-0.2, min(0.2, expectancy))
            
            # Final probability clamp between 0.5 and 0.95
            return max(0.5, min(0.95, win_rate + boost))
            
        except Exception as e:
            logger.error(f"Failed to generate Bayesian confidence: {e}")
            return 0.55

    async def adjust_confidence(self, prior: float, outcome: str, r_multiple: float) -> float:
        """
        Update confidence based on direct market feedback
        """
        if outcome == "HIT_TP":
            adjusted = min(0.99, prior + (self.LEARNING_RATE * r_multiple))
        elif outcome == "HIT_SL":
            adjusted = max(0.01, prior - self.LEARNING_RATE)
        else: # EXPIRED
            adjusted = prior * 0.99 # Decay for non-events
            
        return round(float(adjusted), 4)

    async def update_pattern_stats(self, pattern_hash: str, asset: str, timeframe: str, outcome: str, r: float):
        """
        Update the behavioral memory for a specific pattern
        """
        try:
            # Note: This would typically be a Supabase RPC or upsert
            # Simplified flow for Internal Alpha:
            logger.info(f"🧠 Updating Pattern Memory: {pattern_hash[:8]} | Outcome: {outcome} | R: {r}")
            
            # Logic would involve fetching current stats, calculating new expectancy, and saving
            # To be implemented with Supabase SDK in Phase 2
            pass
        except Exception as e:
            logger.error(f"Pattern update failed: {e}")
