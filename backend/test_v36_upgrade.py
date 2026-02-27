
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer

def test_upgrade():
    analyzer = ContinuousAnalyzer()
    print("Running Analysis Cycle with v3.6 Strategy...")
    analyzer.run_cycle()
    print("Cycle complete.")

if __name__ == "__main__":
    test_upgrade()
