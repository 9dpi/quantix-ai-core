web: sh -c "uvicorn quantix_core.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"
analyzer: python -m quantix_core.engine.continuous_analyzer
watcher: python run_signal_watcher.py
validator: python run_pepperstone_validator.py
