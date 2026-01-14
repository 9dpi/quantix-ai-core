"""
Quantix AI Core v3.2 - Continuous Learning Engine
==================================================
The Brain. Learns from OUTCOMES, not from candles.

Key Principles:
- NO black-box ML
- Explainable rules
- Auditable decisions
- Stats-based confidence adjustment
"""

from typing import Dict, Optional
from datetime import datetime
import hashlib


class LearningEngine:
    """
    Quantix Learning Engine.
    
    This is NOT a neural network. It's a rule-based system that:
    1. Tracks pattern performance
    2. Adjusts confidence weights based on outcomes
    3. Provides explainable reasoning
    """
    
    # Learning rules (Explainable AI)
    RULES = {
        'poor_performance': {
            'condition': lambda stats: stats['win_rate'] < 0.45 and stats['sample_size'] >= 30,
            'adjustment': -0.3,
            'reason': 'Pattern shows poor win rate with sufficient sample size'
        },
        'strong_overlap': {
            'condition': lambda stats: stats['win_rate'] > 0.60 and stats['sample_size'] >= 20 and stats.get('session') == 'overlap',
            'adjustment': +0.2,
            'reason': 'Strong performance during London-NY overlap'
        },
        'extreme_volatility': {
            'condition': lambda stats: stats.get('volatility_state') == 'extreme',
            'adjustment': -0.2,
            'reason': 'Extreme volatility reduces pattern reliability'
        },
        'consistent_winner': {
            'condition': lambda stats: stats['win_rate'] > 0.65 and stats['sample_size'] >= 50,
            'adjustment': +0.3,
            'reason': 'Proven consistent performance over large sample'
        },
        'new_pattern': {
            'condition': lambda stats: stats['sample_size'] < 10,
            'adjustment': -0.1,
            'reason': 'Insufficient data - conservative approach'
        }
    }
    
    def __init__(self, db_connection):
        """
        Initialize Learning Engine.
        
        Args:
            db_connection: Database connection for reading/writing learning memory
        """
        self.db = db_connection
    
    def generate_pattern_hash(self, context: Dict) -> str:
        """
        Generate unique hash for a pattern context.
        
        Args:
            context: Dict with keys like asset, timeframe, session, volatility, etc.
        
        Returns:
            64-character hash string
        """
        # Create deterministic string from context
        context_str = f"{context.get('asset', '')}_{context.get('timeframe', '')}_{context.get('session', '')}_{context.get('volatility_state', '')}"
        
        # Add pattern-specific features if available
        if 'pattern_type' in context:
            context_str += f"_{context['pattern_type']}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(context_str.encode()).hexdigest()
    
    async def calculate_confidence(self, pattern_hash: str, base_confidence: float = 0.75) -> Dict:
        """
        Calculate adjusted confidence for a pattern.
        
        Args:
            pattern_hash: Pattern identifier
            base_confidence: Initial confidence (0.0 to 1.0)
        
        Returns:
            Dict with:
            - adjusted_confidence: Final confidence after learning
            - confidence_weight: Multiplier from learning memory
            - explanation: Human-readable reason
        """
        # Fetch learning memory for this pattern
        memory = await self._get_learning_memory(pattern_hash)
        
        if memory is None:
            # New pattern - no history
            return {
                'adjusted_confidence': base_confidence * 0.9,  # Slightly conservative
                'confidence_weight': 0.9,
                'explanation': 'New pattern - no historical data. Using conservative confidence.'
            }
        
        # Apply confidence weight from learning memory
        adjusted_confidence = base_confidence * memory['confidence_weight']
        
        # Clamp to valid range
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        return {
            'adjusted_confidence': adjusted_confidence,
            'confidence_weight': memory['confidence_weight'],
            'win_rate': memory['win_rate'],
            'sample_size': memory['total_signals'],
            'explanation': memory.get('adjustment_reason', 'Learning-based adjustment')
        }
    
    async def update_from_outcome(self, signal_outcome: Dict) -> Dict:
        """
        Update learning memory after a signal outcome.
        
        This is called when a signal hits TP, SL, or expires.
        
        Args:
            signal_outcome: Dict with outcome data (result, pips, pattern_hash, etc.)
        
        Returns:
            Dict with update summary
        """
        pattern_hash = signal_outcome['pattern_hash']
        
        # Get current memory
        memory = await self._get_learning_memory(pattern_hash)
        
        if memory is None:
            # Create new memory entry
            memory = await self._create_learning_memory(signal_outcome)
        else:
            # Update existing memory
            memory = await self._update_learning_memory(memory, signal_outcome)
        
        # Apply learning rules
        new_weight, applied_rules = self._apply_learning_rules(memory)
        
        # Update confidence weight in database
        await self._save_confidence_weight(pattern_hash, new_weight, applied_rules)
        
        return {
            'pattern_hash': pattern_hash,
            'old_weight': memory.get('confidence_weight', 1.0),
            'new_weight': new_weight,
            'applied_rules': applied_rules,
            'win_rate': memory['win_rate'],
            'sample_size': memory['total_signals']
        }
    
    def _apply_learning_rules(self, memory: Dict) -> tuple:
        """
        Apply explainable learning rules to adjust confidence.
        
        Returns:
            (new_weight, applied_rules)
        """
        base_weight = 1.0
        applied_rules = []
        
        for rule_name, rule in self.RULES.items():
            if rule['condition'](memory):
                base_weight += rule['adjustment']
                applied_rules.append({
                    'rule': rule_name,
                    'adjustment': rule['adjustment'],
                    'reason': rule['reason']
                })
        
        # Clamp weight to reasonable range (0.5 to 1.5)
        new_weight = max(0.5, min(1.5, base_weight))
        
        return new_weight, applied_rules
    
    async def _get_learning_memory(self, pattern_hash: str) -> Optional[Dict]:
        """Fetch learning memory from database."""
        result = await self.db.fetch_one(
            "SELECT * FROM learning_memory WHERE pattern_hash = $1",
            pattern_hash
        )
        return dict(result) if result else None
    
    async def _create_learning_memory(self, signal_outcome: Dict) -> Dict:
        """Create new learning memory entry."""
        # This is typically handled by the database trigger
        # But we return the expected structure
        return {
            'pattern_hash': signal_outcome['pattern_hash'],
            'asset': signal_outcome['asset'],
            'timeframe': signal_outcome['timeframe'],
            'session': signal_outcome.get('session'),
            'volatility_state': signal_outcome.get('volatility_state'),
            'total_signals': 1,
            'total_wins': 1 if signal_outcome['result'] == 'TP' else 0,
            'total_losses': 1 if signal_outcome['result'] == 'SL' else 0,
            'total_expired': 1 if signal_outcome['result'] == 'EXPIRED' else 0,
            'win_rate': 1.0 if signal_outcome['result'] == 'TP' else 0.0,
            'confidence_weight': 1.0
        }
    
    async def _update_learning_memory(self, memory: Dict, signal_outcome: Dict) -> Dict:
        """Update existing learning memory with new outcome."""
        # Increment counters
        memory['total_signals'] += 1
        
        if signal_outcome['result'] == 'TP':
            memory['total_wins'] += 1
        elif signal_outcome['result'] == 'SL':
            memory['total_losses'] += 1
        elif signal_outcome['result'] == 'EXPIRED':
            memory['total_expired'] += 1
        
        # Recalculate win rate
        memory['win_rate'] = memory['total_wins'] / memory['total_signals']
        
        return memory
    
    async def _save_confidence_weight(self, pattern_hash: str, new_weight: float, applied_rules: list):
        """Save updated confidence weight to database."""
        reason = '; '.join([r['reason'] for r in applied_rules]) if applied_rules else 'No rules applied'
        
        await self.db.execute(
            """
            UPDATE learning_memory
            SET 
                confidence_weight = $1,
                last_adjustment = NOW(),
                adjustment_reason = $2,
                updated_at = NOW()
            WHERE pattern_hash = $3
            """,
            new_weight, reason, pattern_hash
        )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("Quantix Learning Engine - Explainable AI")
    print("=" * 60)
    
    # Example: Apply learning rules to a pattern
    example_memory = {
        'pattern_hash': 'abc123',
        'asset': 'EURUSD',
        'timeframe': 'm15',
        'session': 'overlap',
        'volatility_state': 'normal',
        'total_signals': 50,
        'total_wins': 33,
        'total_losses': 15,
        'total_expired': 2,
        'win_rate': 0.66,
        'confidence_weight': 1.0
    }
    
    # Simulate learning engine (without DB)
    class MockDB:
        async def fetch_one(self, *args): return None
        async def execute(self, *args): pass
    
    engine = LearningEngine(MockDB())
    new_weight, applied_rules = engine._apply_learning_rules(example_memory)
    
    print(f"\nPattern Performance:")
    print(f"  Win Rate: {example_memory['win_rate']:.1%}")
    print(f"  Sample Size: {example_memory['total_signals']}")
    print(f"  Session: {example_memory['session']}")
    
    print(f"\nLearning Adjustment:")
    print(f"  Old Weight: {example_memory['confidence_weight']:.2f}")
    print(f"  New Weight: {new_weight:.2f}")
    
    print(f"\nApplied Rules:")
    for rule in applied_rules:
        print(f"  • {rule['rule']}: {rule['adjustment']:+.2f} ({rule['reason']})")
