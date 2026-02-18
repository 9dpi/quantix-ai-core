web: PYTHONPATH=backend uvicorn quantix_core.api.main:app --host 0.0.0.0 --port $PORT --proxy-headers
analyzer: PYTHONPATH=backend python -m quantix_core.engine.continuous_analyzer
watcher: PYTHONPATH=backend python backend/run_signal_watcher.py
validator: PYTHONPATH=backend python backend/run_pepperstone_validator.py
