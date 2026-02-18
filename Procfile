web: uvicorn minimal_app:app --host 0.0.0.0 --port $PORT --proxy-headers
analyzer: python -m quantix_core.engine.continuous_analyzer
watcher: python run_signal_watcher.py
validator: python run_pepperstone_validator.py
