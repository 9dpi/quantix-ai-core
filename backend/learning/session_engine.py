"""
Quantix AI Core v3.2 - Session Intelligence Engine
===================================================
Internal session detection and scoring.
NO external API needed.

Purpose:
- Identify trading session
- Score session favorability
- Explain "Why this time is favorable"
"""

from datetime import datetime, time
from typing import Dict, Tuple
import pytz


class SessionEngine:
    """
    Internal session intelligence.
    
    Provides context about market conditions based on time alone.
    """
    
    # Session definitions (UTC)
    SESSIONS = {
        'london': {
            'start': time(7, 0),
            'end': time(16, 0),
            'score': 0.85,
            'description': 'London session - High liquidity, institutional activity'
        },
        'newyork': {
            'start': time(13, 0),
            'end': time(22, 0),
            'score': 0.90,
            'description': 'New York session - Highest volume, trend continuation'
        },
        'overlap': {
            'start': time(13, 0),
            'end': time(16, 0),
            'score': 1.0,
            'description': 'London-NY overlap - Peak liquidity, best execution'
        },
        'asia': {
            'start': time(0, 0),
            'end': time(7, 0),
            'score': 0.50,
            'description': 'Asian session - Lower volatility, range-bound'
        },
        'off_hours': {
            'start': None,
            'end': None,
            'score': 0.30,
            'description': 'Off-hours - Thin liquidity, avoid trading'
        }
    }
    
    def get_session(self, timestamp: datetime = None) -> Dict:
        """
        Get current session information.
        
        Args:
            timestamp: Optional datetime. If None, uses current UTC time.
        
        Returns:
            Dict with keys:
            - name: Session name
            - score: Favorability score (0.0 to 1.0)
            - description: Human-readable explanation
            - is_favorable: Boolean (True if score >= 0.8)
        """
        if timestamp is None:
            timestamp = datetime.now(pytz.UTC)
        
        utc_time = timestamp.astimezone(pytz.UTC).time()
        
        # Check overlap first (highest priority)
        if self._time_in_session(utc_time, 'overlap'):
            session_info = self.SESSIONS['overlap']
            return {
                'name': 'overlap',
                'score': session_info['score'],
                'description': session_info['description'],
                'is_favorable': True,
                'timestamp': timestamp
            }
        
        # Check London
        if self._time_in_session(utc_time, 'london'):
            session_info = self.SESSIONS['london']
            return {
                'name': 'london',
                'score': session_info['score'],
                'description': session_info['description'],
                'is_favorable': True,
                'timestamp': timestamp
            }
        
        # Check New York
        if self._time_in_session(utc_time, 'newyork'):
            session_info = self.SESSIONS['newyork']
            return {
                'name': 'newyork',
                'score': session_info['score'],
                'description': session_info['description'],
                'is_favorable': True,
                'timestamp': timestamp
            }
        
        # Check Asia
        if self._time_in_session(utc_time, 'asia'):
            session_info = self.SESSIONS['asia']
            return {
                'name': 'asia',
                'score': session_info['score'],
                'description': session_info['description'],
                'is_favorable': False,
                'timestamp': timestamp
            }
        
        # Off hours
        session_info = self.SESSIONS['off_hours']
        return {
            'name': 'off_hours',
            'score': session_info['score'],
            'description': session_info['description'],
            'is_favorable': False,
            'timestamp': timestamp
        }
    
    def explain_favorability(self, timestamp: datetime = None) -> str:
        """
        Generate human-readable explanation of why this time is favorable.
        
        Returns:
            String explanation for "Why this trade?" section
        """
        session = self.get_session(timestamp)
        
        if session['name'] == 'overlap':
            return (
                "London-New York overlap detected. This 3-hour window (13:00-16:00 UTC) "
                "offers peak market liquidity and institutional participation. "
                "Price action is most reliable during this period, with tighter spreads "
                "and higher probability of trend continuation."
            )
        
        elif session['name'] == 'london':
            return (
                "London session active. European institutional flows dominate, "
                "providing strong directional moves. Volatility is elevated but controlled. "
                "Suitable for momentum-based strategies."
            )
        
        elif session['name'] == 'newyork':
            return (
                "New York session active. U.S. economic data releases and institutional "
                "order flow create strong trends. Highest daily volume occurs during this window. "
                "Ideal for breakout and trend-following strategies."
            )
        
        elif session['name'] == 'asia':
            return (
                "Asian session detected. Market activity is subdued with lower volatility. "
                "Price tends to range rather than trend. Confidence is reduced during this period. "
                "Consider waiting for London open."
            )
        
        else:  # off_hours
            return (
                "Off-hours period. Liquidity is thin and spreads are wide. "
                "Price movements are unreliable and may be driven by algorithmic activity "
                "rather than genuine market sentiment. Trading is NOT recommended."
            )
    
    def should_learn(self, timestamp: datetime = None) -> bool:
        """
        Determine if Quantix should learn from data at this time.
        
        Learning is DISABLED during:
        - Off-hours
        - Low-score sessions (Asia)
        
        Returns:
            True if learning should be enabled
        """
        session = self.get_session(timestamp)
        return session['is_favorable']
    
    def _time_in_session(self, check_time: time, session_name: str) -> bool:
        """Check if time falls within a session."""
        session = self.SESSIONS[session_name]
        start = session['start']
        end = session['end']
        
        if start is None or end is None:
            return False
        
        if start <= end:
            return start <= check_time <= end
        else:  # Crosses midnight
            return check_time >= start or check_time <= end


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    engine = SessionEngine()
    
    # Test different times
    test_times = [
        datetime(2026, 1, 14, 14, 30, tzinfo=pytz.UTC),  # 2:30 PM UTC (Overlap)
        datetime(2026, 1, 14, 10, 0, tzinfo=pytz.UTC),   # 10 AM UTC (London)
        datetime(2026, 1, 14, 20, 0, tzinfo=pytz.UTC),   # 8 PM UTC (NY)
        datetime(2026, 1, 14, 3, 0, tzinfo=pytz.UTC),    # 3 AM UTC (Asia)
        datetime(2026, 1, 14, 23, 0, tzinfo=pytz.UTC),   # 11 PM UTC (Off-hours)
    ]
    
    for test_time in test_times:
        session = engine.get_session(test_time)
        should_learn = engine.should_learn(test_time)
        
        print(f"\n{'='*60}")
        print(f"Time: {test_time.strftime('%H:%M UTC')}")
        print(f"Session: {session['name'].upper()}")
        print(f"Score: {session['score']:.2f}")
        print(f"Favorable: {session['is_favorable']}")
        print(f"Learn from this data: {should_learn}")
        print(f"\nExplanation:")
        print(engine.explain_favorability(test_time))
