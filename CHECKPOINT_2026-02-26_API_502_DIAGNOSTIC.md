# CHECKPOINT: API 502 Bad Gateway Diagnostic
**Date:** 2026-02-26 08:55 (GMT+7)
**Status:** 🛠️ IN PROGRESS
**Branch:** `main`

## 🎯 OBJECTIVE
Resolve the **502 Bad Gateway** error affecting the Quantix AI Core API layer on Railway.

## 🔍 COMPLETED DIAGNOSTICS
1.  **Launcher Verification**:
    - Script `start_railway_web.py` is executing successfully on Railway.
    - Verified environment variables (Railway provides `$PORT`).
    - Successfully logged `LAUNCHER` and `IMPORT_OK` status to Supabase.
2.  **FastAPI Application Startup**:
    - `main.py` successfully reaches `startup_event`.
    - Logged `SYSTEM_API | ONLINE_PORT_8080` to Supabase.
    - Verified DB connection is active and settings are loaded (`0.0.0.0:8000` internal).
3.  **Dependency Audit**:
    - Removed `asyncio` from `requirements.txt` (standard lib in 3.11).
    - Verified `fastapi`, `uvicorn`, and `supabase` are present.
4.  **Network Configuration**:
    - Switched `uvicorn` to include `--proxy-headers` and `--forwarded-allow-ips='*'`.
    - Reverted `Dockerfile` `EXPOSE` to `8080` to match Railway defaults.

## 🛠️ CURRENT IMPLEMENTATION
- **Middleware Logging**: Added `db_log_requests` middleware to `main.py` to capture every incoming request in `fx_analysis_log`.
- **Advanced Launcher**: `start_railway_web.py` now includes granular try-except blocks for app import and startup proof.

## 📉 OBSERVATIONS
- Background services (**Watcher**, **Validator**, **Analyzer**) are 🟢 **HEALTHY** and continue to log to Supabase.
- API service is 🔴 **DEGRADED**. Despite logging "ONLINE", external requests receive 502 immediately.
- Current suspicion: Misalignment between Railway Edge Proxy and Uvicorn port binding or an immediate exit of the uvicorn process after the startup log.

## 🚀 NEXT STEPS
1.  **Monitor `SYSTEM_REQ` Logs**: Check if any `GET /` or `GET /api/v1/health` requests appear in Supabase logs.
2.  **Isolate Middleware**: If requests don't appear, temporarily disable all custom middleware to ensure basic connectivity.
3.  **Local Replication**: Attempt to run the exact Docker image locally with a mapped port to verify bridge networking.
4.  **Railway Support/Logs**: Access direct Railway deployment logs to see if uvicorn is printing error tracebacks not captured by the `subprocess.run` wrapper.

---
*Checkpoint created to preserve the technical state before further invasive changes.*
