"""
Quantix Learning Lab - Decision Advisor
EXPERIMENTAL / SANDBOX ONLY
Mapping logic for Buy/Sell candidates based on stable structural evidence.
"""

from loguru import logger
from datetime import datetime
import uuid

class LabAdvisor:
    """
    Advisor for the Learning Lab (Sandbox).
    Operates ONLY on analytics snapshots/stats.
    Implemented based on SIGNAL_ENGINE_LAB_SPEC.md v1.
    """
    
    def __init__(self):
        self.min_confidence = 0.9
        self.min_dominance = 0.65
        self.min_persistence = 2
        self.lab_version = "signal_mapping_v1"

    def advise(self, snapshot: dict) -> dict:
        """
        Map structural state to Buy/Sell candidates using explicit rules.
        """
        signal_id = f"LAB-{uuid.uuid4().hex[:8]}"
        state = snapshot.get("structure_state", "unknown").upper()
        conf = snapshot.get("confidence", 0)
        dom = snapshot.get("dominance", 0)
        
        # In v1, persistence and fake_breakout are derived or passed in snapshot
        # For this draft, we pull them from snapshot or default to safety
        persistence = snapshot.get("persistence", 2) 
        fake_breakout = snapshot.get("evidence", {}).get("fake_breakout", False)
        
        logger.info(f"🧪 [Lab] Evaluating Mapping: {state} (Conf: {conf}, Dom: {dom}, Persist: {persistence})")
        
        classification = "NO_ACTION"
        reason = "Structure not reliable or thresholds not met"
        
        # 2.2 Concrete Thresholds (Mapped exactly from Spec)
        is_eligible = (
            conf >= self.min_confidence and 
            dom >= self.min_dominance and 
            persistence >= self.min_persistence and
            not fake_breakout
        )

        if is_eligible:
            if state == "BULLISH":
                classification = "BUY_CANDIDATE"
                reason = "Sustained bullish structure with high dominance"
            elif state == "BEARISH":
                classification = "SELL_CANDIDATE"
                reason = "Sustained bearish structure with high dominance"
        
        # Build auditable signal
        signal = {
            "signal_id": f"LAB_{snapshot['asset']}_{snapshot['timeframe']}_{datetime.now().strftime('%Y%m%dT%H')}",
            "classification": classification,
            "confidence": conf,
            "reason": reason,
            "structure_state": state.lower(),
            "expires_in": "2 candles",
            "lab_only": True,
            "audit": {
                "snapshot_id": snapshot.get("snapshot_id", "manual"),
                "ruleset": self.lab_version
            },
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if classification != "NO_ACTION":
            logger.success(f"🧪 [Lab] 🎯 Candidate Generated: {classification}")
        
        return signal
