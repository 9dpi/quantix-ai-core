"""
Quantix AI Core - Railway Deployment Monitor
Monitors API health and logs deployment status
"""

import requests
import time
from datetime import datetime
import sys

API_BASE = "https://quantixaicore-production.up.railway.app"
ENDPOINTS = {
    "root": f"{API_BASE}/",
    "health": f"{API_BASE}/api/v1/health",
    "feature_health": f"{API_BASE}/api/v1/internal/feature-state/health",
    "structure": f"{API_BASE}/api/v1/internal/feature-state/structure?symbol=EURUSD&tf=H4"
}

def check_endpoint(name, url, timeout=10):
    """Check if endpoint is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        status = "✅ OK" if response.status_code == 200 else f"⚠️ {response.status_code}"
        return {
            "name": name,
            "status": status,
            "code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds(),
            "error": None
        }
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "status": "❌ TIMEOUT",
            "code": None,
            "success": False,
            "response_time": None,
            "error": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "status": "❌ CONNECTION",
            "code": None,
            "success": False,
            "response_time": None,
            "error": "Connection refused (service may be restarting)"
        }
    except Exception as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "code": None,
            "success": False,
            "response_time": None,
            "error": str(e)
        }

def monitor_deployment(duration_minutes=10, interval_seconds=30):
    """Monitor deployment for specified duration"""
    print("=" * 80)
    print("🚀 QUANTIX AI CORE - RAILWAY DEPLOYMENT MONITOR")
    print("=" * 80)
    print(f"⏱️  Monitoring for {duration_minutes} minutes (checks every {interval_seconds}s)")
    print(f"🎯 Target: {API_BASE}")
    print("=" * 80)
    print()
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    check_count = 0
    success_count = 0
    
    while time.time() < end_time:
        check_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = int(time.time() - start_time)
        remaining = int(end_time - time.time())
        
        print(f"\n{'='*80}")
        print(f"📊 CHECK #{check_count} | {timestamp} | Elapsed: {elapsed}s | Remaining: {remaining}s")
        print(f"{'='*80}")
        
        all_success = True
        results = []
        
        for name, url in ENDPOINTS.items():
            result = check_endpoint(name, url)
            results.append(result)
            
            status_icon = result["status"]
            response_time = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
            
            print(f"{status_icon:15} | {name:20} | {response_time:8} | {url}")
            
            if result['error']:
                print(f"               └─ Error: {result['error']}")
            
            if not result['success']:
                all_success = False
        
        if all_success:
            success_count += 1
            print(f"\n✅ All endpoints healthy! (Success streak: {success_count})")
        else:
            success_count = 0
            print(f"\n⚠️  Some endpoints failed - Service may be restarting")
        
        # Check if we should stop early (3 consecutive successes)
        if success_count >= 3:
            print(f"\n{'='*80}")
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print(f"{'='*80}")
            print(f"✅ All endpoints responded successfully 3 times in a row")
            print(f"✅ Service is stable and ready for production")
            print(f"⏱️  Total monitoring time: {elapsed}s")
            print()
            return True
        
        # Wait before next check
        if time.time() < end_time:
            print(f"\n⏳ Waiting {interval_seconds}s before next check...")
            time.sleep(interval_seconds)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 MONITORING COMPLETE")
    print(f"{'='*80}")
    print(f"Total checks: {check_count}")
    print(f"Duration: {duration_minutes} minutes")
    
    if success_count > 0:
        print(f"✅ Service appears to be running (last {success_count} checks successful)")
        return True
    else:
        print(f"⚠️  Service may still be deploying or experiencing issues")
        return False

def quick_check():
    """Quick one-time check of all endpoints"""
    print("=" * 80)
    print("🔍 QUICK HEALTH CHECK")
    print("=" * 80)
    print()
    
    all_success = True
    for name, url in ENDPOINTS.items():
        result = check_endpoint(name, url)
        status_icon = result["status"]
        response_time = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
        
        print(f"{status_icon:15} | {name:20} | {response_time:8}")
        
        if result['error']:
            print(f"               └─ {result['error']}")
        
        if not result['success']:
            all_success = False
    
    print()
    if all_success:
        print("✅ All systems operational!")
    else:
        print("⚠️  Some systems are not responding")
    
    return all_success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_check()
    else:
        monitor_deployment(duration_minutes=10, interval_seconds=30)
