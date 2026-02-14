"""
Validation Results Analyzer
Analyzes validation logs to generate insights and recommendations
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

VALIDATION_LOG = Path(__file__).parent / "validation_discrepancies.jsonl"


def load_discrepancies() -> List[Dict]:
    """Load all discrepancies from JSONL file"""
    if not VALIDATION_LOG.exists():
        print("⚠️  No validation log found. Run validator first.")
        return []
    
    discrepancies = []
    with open(VALIDATION_LOG, 'r') as f:
        for line in f:
            if line.strip():
                discrepancies.append(json.loads(line))
    
    return discrepancies


def analyze_discrepancies(discrepancies: List[Dict]):
    """Generate comprehensive analysis report"""
    
    if not discrepancies:
        print("✅ No discrepancies found! System is 100% accurate.")
        return
    
    print("=" * 80)
    print("  VALIDATION ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    # Basic stats
    total = len(discrepancies)
    unique_signals = len(set(d['signal_id'] for d in discrepancies))
    
    print(f"📊 Overview:")
    print(f"   Total discrepancies: {total}")
    print(f"   Affected signals: {unique_signals}")
    print()
    
    # By type
    by_type = defaultdict(int)
    for d in discrepancies:
        by_type[d['type']] += 1
    
    print(f"📈 By Type:")
    for dtype, count in by_type.items():
        percentage = (count / total) * 100
        print(f"   {dtype}: {count} ({percentage:.1f}%)")
    print()
    
    # Time distribution
    print(f"⏰ Time Distribution:")
    by_hour = defaultdict(int)
    for d in discrepancies:
        timestamp = datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00'))
        hour = timestamp.hour
        by_hour[hour] += 1
    
    for hour in sorted(by_hour.keys()):
        count = by_hour[hour]
        bar = "█" * (count * 2)
        print(f"   {hour:02d}:00 | {bar} {count}")
    print()
    
    # Price analysis
    print(f"💰 Price Impact Analysis:")
    
    tp_discrepancies = [d for d in discrepancies if d['type'] == 'TP_MISMATCH']
    sl_discrepancies = [d for d in discrepancies if d['type'] == 'SL_MISMATCH']
    
    if tp_discrepancies:
        tp_diffs = []
        for d in tp_discrepancies:
            tp_price = d.get('tp_price', 0)
            market_high = d.get('market_high', 0)
            market_low = d.get('market_low', 0)
            diff = abs(market_high - tp_price)
            tp_diffs.append(diff * 10000)  # Convert to pips
        
        avg_diff = sum(tp_diffs) / len(tp_diffs)
        max_diff = max(tp_diffs)
        print(f"   TP discrepancies:")
        print(f"   - Average: {avg_diff:.2f} pips")
        print(f"   - Maximum: {max_diff:.2f} pips")
    
    if sl_discrepancies:
        sl_diffs = []
        for d in sl_discrepancies:
            sl_price = d.get('sl_price', 0)
            market_high = d.get('market_high', 0)
            market_low = d.get('market_low', 0)
            diff = abs(market_low - sl_price)
            sl_diffs.append(diff * 10000)
        
        avg_diff = sum(sl_diffs) / len(sl_diffs)
        max_diff = max(sl_diffs)
        print(f"   SL discrepancies:")
        print(f"   - Average: {avg_diff:.2f} pips")
        print(f"   - Maximum: {max_diff:.2f} pips")
    
    print()
    
    # Recommendations
    print("=" * 80)
    print("  RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    discrepancy_rate = (unique_signals / max(unique_signals, 1)) * 100
    
    if discrepancy_rate < 5:
        print("✅ EXCELLENT: Discrepancy rate < 5%")
        print("   → Current Binance proxy is highly accurate")
        print("   → Recommend: Stay with current setup")
        print("   → Optional: Add 0.5 pip spread buffer for safety")
    
    elif discrepancy_rate < 10:
        print("⚠️  ACCEPTABLE: Discrepancy rate 5-10%")
        print("   → Binance proxy is mostly accurate")
        print("   → Recommend: Add 0.5-1.0 pip spread buffer")
        print("   → Consider: Phase 2 (MT5 integration) if accuracy critical")
    
    else:
        print("❌ HIGH: Discrepancy rate > 10%")
        print("   → Significant differences detected")
        print("   → Recommend: Proceed to Phase 2 (Pepperstone MT5 API)")
        print("   → Action: Review feed source and timing")
    
    print()
    
    # Spread buffer recommendation
    if tp_diffs or sl_diffs:
        all_diffs = (tp_diffs if tp_diffs else []) + (sl_diffs if sl_diffs else [])
        if all_diffs:
            recommended_buffer = max(all_diffs) * 1.5  # 50% safety margin
            print(f"📐 Recommended Spread Buffer: {recommended_buffer:.2f} pips")
            print(f"   (Based on max observed discrepancy + 50% margin)")
    
    print()


def export_summary(discrepancies: List[Dict]):
    """Export summary to JSON for dashboard"""
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_discrepancies": len(discrepancies),
        "unique_signals": len(set(d['signal_id'] for d in discrepancies)),
        "by_type": {},
        "recommendations": []
    }
    
    # Count by type
    for d in discrepancies:
        dtype = d['type']
        summary['by_type'][dtype] = summary['by_type'].get(dtype, 0) + 1
    
    # Generate recommendations
    discrepancy_rate = (summary['unique_signals'] / max(summary['unique_signals'], 1)) * 100
    
    if discrepancy_rate < 5:
        summary['recommendations'].append("Stay with current Binance proxy")
        summary['recommendations'].append("Add 0.5 pip spread buffer")
    elif discrepancy_rate < 10:
        summary['recommendations'].append("Add 1.0 pip spread buffer")
        summary['recommendations'].append("Consider MT5 integration")
    else:
        summary['recommendations'].append("Proceed to Phase 2 (MT5 API)")
    
    # Save
    output_file = Path(__file__).parent / "validation_summary.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Summary exported to: {output_file}")


def main():
    """Main analysis function"""
    print("Loading validation data...")
    discrepancies = load_discrepancies()
    
    if not discrepancies:
        print("\n✅ No discrepancies found!")
        print("   System is performing perfectly.")
        print("   Recommendation: Continue monitoring for 1-2 weeks.")
        return
    
    print(f"Loaded {len(discrepancies)} discrepancies\n")
    
    analyze_discrepancies(discrepancies)
    export_summary(discrepancies)


if __name__ == "__main__":
    main()
