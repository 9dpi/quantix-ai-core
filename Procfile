# Build trigger 2026-03-05 10:50+0700
web: PYTHONPATH=backend python -m uvicorn quantix_core.api.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
watcher: python start_railway_watcher.py
validator: python start_railway_validator.py
watchdog: python start_railway_watchdog.py
