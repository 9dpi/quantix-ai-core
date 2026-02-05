web: uvicorn backend.quantix_core.api.main:app --host 0.0.0.0 --port $PORT
analyzer: python -m quantix_core.engine.continuous_analyzer
watcher: python backend/run_signal_watcher.py
