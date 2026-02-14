"""
QUANTIX CROSS-PLATFORM AUDIT - Frontend Compliance Check
Validates that all display channels read ONLY release_confidence
"""

import os
import re

print("=" * 80)
print("QUANTIX FRONTEND AUDIT - IMMUTABLE RULE COMPLIANCE")
print("=" * 80)
print()

# ============================================================================
# 1. TELEGRAM NOTIFIER CHECK
# ============================================================================
print("1. TELEGRAM NOTIFIER (Backend)")
print("-" * 80)

telegram_file = r"d:\Automator_Prj\Quantix_AI_Core\backend\quantix_core\notifications\telegram_notifier_v2.py"

with open(telegram_file, 'r', encoding='utf-8') as f:
    content = f.read()
    
# Check for IMMUTABLE RULE comment
if "IMMUTABLE RULE" in content and "release_confidence" in content:
    print("✅ PASS: IMMUTABLE RULE comment found")
    
# Check for forbidden patterns
forbidden_patterns = [
    (r'ai_confidence(?!\s*#)', 'Direct use of ai_confidence'),
    (r'confidence\s*\|\|', 'Fallback logic detected'),
]

violations = []
for pattern, desc in forbidden_patterns:
    matches = re.finditer(pattern, content, re.IGNORECASE)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        violations.append(f"   Line {line_num}: {desc}")

if not violations:
    print("✅ PASS: No forbidden confidence patterns")
else:
    print("❌ FAIL: Found violations:")
    for v in violations:
        print(v)

print()

# ============================================================================
# 2. DASHBOARD (Telesignal) CHECK
# ============================================================================
print("2. DASHBOARD (Telesignal - Railway)")
print("-" * 80)

dashboard_file = r"d:\Automator_Prj\Telesignal\index.html"

with open(dashboard_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for correct pattern: release_confidence || 0
correct_pattern = r'release_confidence\s*\|\|\s*0'
correct_matches = len(re.findall(correct_pattern, content))

# Check for forbidden fallback chains
forbidden_pattern = r'ai_confidence\s*\|\|.*release_confidence'
forbidden_matches = re.findall(forbidden_pattern, content)

if correct_matches >= 2:  # Should have at least 2 (active + history)
    print(f"✅ PASS: Found {correct_matches} correct uses of 'release_confidence || 0'")
else:
    print(f"⚠️  WARNING: Only {correct_matches} uses of release_confidence")

if not forbidden_matches:
    print("✅ PASS: No forbidden fallback chains (ai_confidence || release_confidence)")
else:
    print(f"❌ FAIL: Found {len(forbidden_matches)} forbidden fallback patterns")
    for match in forbidden_matches[:3]:
        print(f"   - {match}")

print()

# ============================================================================
# 3. PUBLIC WEBSITE (quantix-live-execution) CHECK
# ============================================================================
print("3. PUBLIC WEBSITE (signalgeniusai.com)")
print("-" * 80)

website_file = r"d:\Automator_Prj\Quantix_MPV\quantix-live-execution\signal_record.js"

with open(website_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for correct pattern
correct_pattern = r'release_confidence\s*\|\|\s*0'
correct_matches = len(re.findall(correct_pattern, content))

# Check for forbidden patterns
forbidden_pattern = r'ai_confidence'
forbidden_matches = re.findall(forbidden_pattern, content, re.IGNORECASE)

if correct_matches >= 1:
    print(f"✅ PASS: Found {correct_matches} correct uses of 'release_confidence || 0'")
else:
    print(f"⚠️  WARNING: No uses of release_confidence found")

if not forbidden_matches:
    print("✅ PASS: No references to ai_confidence")
else:
    print(f"❌ FAIL: Found {len(forbidden_matches)} references to ai_confidence")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("FRONTEND AUDIT SUMMARY")
print("=" * 80)
print()
print("All display channels (Telegram, Dashboard, Website) have been audited.")
print("✅ = Compliant with IMMUTABLE RULE")
print("❌ = Violations detected")
print("⚠️  = Warnings (review recommended)")
print()
print("=" * 80)
