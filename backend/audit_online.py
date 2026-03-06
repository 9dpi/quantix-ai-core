import requests
import json
from datetime import datetime
import os

# Configuration
API_GATEWAY = "https://quantixapiserver-production.up.railway.app"
HEALTH_ENDPOINT = f"{API_GATEWAY}/api/v1/health"
SIGNALS_ENDPOINT = f"{API_GATEWAY}/api/v1/signals?limit=5"

def audit_online():
    report = []
    report.append("="*55)
    report.append("   GLOBAL QUANTIX AI CORE - ONLINE PRODUCTION AUDIT")
    report.append(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("="*55)
    report.append("")

    # 1. Health Check (API Gateway)
    print(f"[*] Checking API Gateway: {API_GATEWAY}...")
    try:
        start_time = datetime.now()
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "ONLINE")
            report.append(f"--- [1/2] GATEWAY HEALTH: ONLINE ---")
            report.append(f"Latency: {latency:.0f}ms")
            report.append(f"Version: {data.get('version', 'N/A')}")
            # Try to get backend services status if provided by health endpoint
            services = data.get("services", {})
            if services:
                for svc, s_status in services.items():
                    report.append(f" - {svc}: {s_status}")
            print("OK: Gateway is healthy.")
        else:
            report.append(f"--- [1/2] GATEWAY HEALTH: ERROR ---")
            report.append(f"HTTP Status: {response.status_code}")
            print(f"ERROR: Gateway returned status {response.status_code}")
    except Exception as e:
        report.append(f"--- [1/2] GATEWAY HEALTH: FAIL ---")
        report.append(f"Connection Error: {str(e)}")
        print(f"FAIL: Failed to connect to Gateway: {e}")

    report.append("")

    # 2. Live Signals Audit
    print("[*] Auditing Live Signals via API...")
    try:
        response = requests.get(SIGNALS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            signals = response.json()
            report.append(f"--- [2/2] LIVE SIGNALS (Last 5) ---")
            if not signals:
                report.append("No active signals found in last batch.")
            else:
                for sig in signals:
                    asset = sig.get("asset", "UNK")
                    direction = sig.get("direction", "???")
                    state = sig.get("status", "UNKNOWN")
                    gen_at = sig.get("generated_at", "N/A")[11:16]
                    conf = sig.get("ai_confidence", 0) * 100
                    report.append(f"[{gen_at}] {asset:7} | {direction:4} | {state:15} | Conf: {conf:.0f}%")
            print("✅ Signals audited successfully.")
        else:
            report.append(f"--- [2/2] LIVE SIGNALS: 🔴 FETCH FAILED ---")
            report.append(f"HTTP Status: {response.status_code}")
    except Exception as e:
        report.append(f"--- [2/2] LIVE SIGNALS: 🔴 ERROR ---")
        report.append(f"Error: {str(e)}")

    report.append("")
    report.append("="*55)
    report.append("   ✅ ONLINE AUDIT COMPLETED")
    report.append("="*55)

    result_text = "\n".join(report)
    
    # Save to file
    with open("audit_result_online.txt", "w", encoding="utf-8") as f:
        f.write(result_text)
    
    return result_text

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(audit_online())
