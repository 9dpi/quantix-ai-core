import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

port = os.environ.get("PORT", "8080")
print(f"--- Quantix Launcher ---")
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")
print(f"Starting uvicorn on port {port}...")

cmd = [sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", "--host", "0.0.0.0", "--port", port, "--proxy-headers"]
subprocess.run(cmd)
