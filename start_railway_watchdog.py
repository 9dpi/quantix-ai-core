import os
import sys
import subprocess
from loguru import logger

def main():
    # Set workdir to absolute root
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    
    # 1. Setup PYTHONPATH
    backend_path = os.path.join(root, "backend")
    sys.path.append(backend_path)
    os.environ["PYTHONPATH"] = backend_path
    
    logger.info(f"Setting up Watchdog... root={root}")
    
    # Run the watchdog
    # Using python -m to avoid import issues
    cmd = [sys.executable, "-m", "quantix_core.engine.watchdog"]
    
    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user.")
    except Exception as e:
        logger.error(f"Watchdog crash: {e}")

if __name__ == "__main__":
    main()
