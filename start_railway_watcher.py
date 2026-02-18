import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Watcher Launcher ---")
print(f"CWD: {os.getcwd()}")

# Watcher is a script in backend folder
script_path = os.path.join(backend_path, "run_signal_watcher.py")
cmd = [sys.executable, script_path]
subprocess.run(cmd)
