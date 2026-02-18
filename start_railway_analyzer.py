import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Analyzer Launcher ---")
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")

cmd = [sys.executable, "-m", "quantix_core.engine.continuous_analyzer"]
subprocess.run(cmd)
