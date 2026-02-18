import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Validator Launcher ---")
print(f"CWD: {os.getcwd()}")

# Validator is a script in backend folder
script_path = os.path.join(backend_path, "run_pepperstone_validator.py")
cmd = ["python", script_path]
subprocess.run(cmd)
