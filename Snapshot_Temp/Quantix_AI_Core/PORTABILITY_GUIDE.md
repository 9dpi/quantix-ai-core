
# 📦 Quantix AI Core - Portability Guide

This guide explains how to move and setup the **Quantix AI Core** (The Miner & Learning Engine) to a new environment.

## 1. Prerequisites
- **Python 3.10** or higher installed.
- **Git** (optional, for syncing with GitHub).
- Active internet connection.

## 2. Directory Structure
Copy the following folders/files to your new location:
- `/backend/quantix_core/` (Core Engine & Logic)
- `/backend/.env` (Configuration)
- `/backend/analyze_heartbeat.py` (Learning Script)
- `/backend/heartbeat_audit.jsonl` (Historical Learning Data - **IMPORTANT**)
- `/dashboard/` (For visual reporting)

## 3. Installation
Open terminal in the new directory and run:
```bash
cd backend
pip install -r requirements.txt
```

## 4. Configuration
Ensure your `.env` file contains valid keys:
- `TWELVE_DATA_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ENABLE_LIVE_SIGNAL=true`
- `MONITOR_INTERVAL_SECONDS=120`

## 5. Launching
To start the Miner and the Self-Learning loop:
```bash
python -m quantix_core.api.main
```

---
*Quantix AI Core © 2026 - Autonomous Intelligence Framework*
