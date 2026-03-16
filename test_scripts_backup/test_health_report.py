
import os
import sys
from datetime import datetime, timezone
from loguru import logger

# Add backend to path
project_root = "d:/Automator_Prj/Quantix_AI_Core"
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
from quantix_core.config.settings import settings

print("🚀 Testing Health Report Broadcast...")

try:
    analyzer = ContinuousAnalyzer()
    analyzer._ensure_engines()
    
    print("Calling _broadcast_comprehensive_report()...")
    analyzer._broadcast_comprehensive_report()
    print("✅ Success! Check Telegram.")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
