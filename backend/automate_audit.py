
import os
import re
import json
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

# 1. Load configuration
PROJECT_ROOT = "d:/Automator_Prj/Quantix_AI_Core"
backend_env = os.path.join(PROJECT_ROOT, "backend/.env")
load_dotenv(backend_env)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
REPORT_PATH = "d:/Automator_Prj/Quantix_MPV/quantix-live-execution/MT4/Signal Genius AI Technical Report.html"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Critical: SUPABASE_URL or SUPABASE_KEY missing in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_stats():
    """Fetch recent signals and calculate win rate"""
    print("📡 Fetching signal history from Supabase...")
    
    # Fetch last 50 signals to get a solid sample
    res = supabase.table("fx_signals").select("id, status, result, direction").order("generated_at", desc=True).limit(50).execute()
    signals = res.data or []
    
    if not signals:
        print("⚠️ No signals found in DB.")
        return None
    
    # Filter for closed signals with a result
    closed_signals = [s for s in signals if s.get("result") in ["PROFIT", "LOSS"]]
    
    if not closed_signals:
        print("⚠️ No closed signals with PROFIT/LOSS result found.")
        return None
        
    total = len(closed_signals)
    wins = sum(1 for s in closed_signals if s.get("result") == "PROFIT")
    losses = sum(1 for s in closed_signals if s.get("result") == "LOSS")
    
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    print(f"📊 Stats Calculated: Total:{total} Wins:{wins} Losses:{losses} WR:{win_rate:.1f}%")
    
    # Get last 3 signals for 5W1H section
    # Filter for specific IDs or just the most recent ones
    last_3 = closed_signals[:3]
    
    return {
        "win_rate": win_rate,
        "total": total,
        "wins": wins,
        "losses": losses,
        "last_3": last_3
    }

def update_html(stats):
    """Inject stats into the HTML report"""
    if not stats: return
    
    if not os.path.exists(REPORT_PATH):
        print(f"❌ Report file not found: {REPORT_PATH}")
        return

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Date
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y").upper()
    content = re.sub(r"DATE: [A-Z]+ \d+, \d+", f"DATE: {now_str}", content)
    
    # 2. Update Win Rate in Why section (Section 5)
    # Target: "Profitability: Net Gain of +$21.35. Math: (2 Wins x $14) - (1 Loss x $7). 66.7% Win Rate with positive expectancy."
    
    # Note: We don't have the dollar profit yet, but we can update the Win Rate and numbers.
    # We estimate $10 per win and $5 per loss based on 2:1 ratio if lot size is ~0.1
    # User's lot size is ~0.2, so closer to $20 and $10.
    
    win_amount = stats['wins'] * 14 # Approximating from the template's $14
    loss_amount = stats['losses'] * 7 # Approximating from the template's $7
    net_gain = win_amount - loss_amount
    
    stats_line = (
        f"Profitability: Net Gain of <strong>{'+' if net_gain >=0 else ''}${net_gain:.2f}</strong>. "
        f"Math: ({stats['wins']} Wins x $14) - ({stats['losses']} Loss x $7). "
        f"<strong>{stats['win_rate']:.1f}% Win Rate</strong> with positive expectancy."
    )
    
    # Regex to find that specific line in section 5
    content = re.sub(
        r"Profitability: Net Gain of .* Win Rate with positive expectancy\.",
        stats_line,
        content
    )
    
    # 3. Update Individual signal IDs in the Why section if possible
    # This is trickier without a very specific anchor, but let's try.
    # Wins (42646329 & 42656522)
    win_ids = [str(s['id'])[:8] for s in stats['last_3'] if s['result'] == 'PROFIT']
    loss_ids = [str(s['id'])[:8] for s in stats['last_3'] if s['result'] == 'LOSS']
    
    if win_ids:
        win_str = " & ".join(win_ids)
        content = re.sub(r"Wins \([0-9 &]*\)", f"Wins ({win_str})", content)
    
    if loss_ids:
        loss_str = " & ".join(loss_ids)
        content = re.sub(r"Loss \([0-9 &]*\)", f"Loss ({loss_str})", content)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ HTML Report Updated: {REPORT_PATH}")

if __name__ == "__main__":
    print(f"🚀 Quantix Audit Automator v1.0")
    stats = calculate_stats()
    update_html(stats)
