# 🏗️ QUANTIX AI CORE - IMPORT ARCHITECTURE

**Status:** 🔒 **FROZEN** - Violations will fail PR  
**Last Updated:** 2026-01-15 09:00 UTC  
**Enforcement:** Mandatory for all contributors

---

## 📐 **ARCHITECTURE RULES**

### ✅ **Rule 1: `learning.primitives` - STRUCTURE ONLY**

```python
# ✅ ALLOWED
from quantix_core.learning.primitives.structure import StructurePrimitive

# ❌ FORBIDDEN
from quantix_core.learning.primitives.swing_detector import SwingPoint
from quantix_core.learning.primitives.structure_events import StructureEvent
```

**Reason:** `learning.primitives` contains ONLY the `StructurePrimitive` class for ML/learning purposes.

---

### ✅ **Rule 2: `engine.primitives` - RUNTIME LOGIC ONLY**

```python
# ✅ ALLOWED
from quantix_core.engine.primitives.swing_detector import SwingPoint
from quantix_core.engine.primitives.structure_events import StructureEvent
from quantix_core.engine.primitives.evidence_scorer import EvidenceScorer
from quantix_core.engine.primitives.fake_breakout_filter import FakeBreakoutFilter
from quantix_core.engine.primitives.state_resolver import StateResolver
```

**Reason:** `engine.primitives` contains runtime feature calculation logic.

---

### ✅ **Rule 3: `api.routes` - NEVER IMPORT `learning` DIRECTLY**

```python
# ✅ ALLOWED (via engine)
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.engine.primitives import StructurePrimitive  # Re-exported from engine

# ❌ FORBIDDEN (direct learning import)
from quantix_core.learning.primitives.structure import StructurePrimitive
```

**Reason:** API routes should access learning components through the engine layer, not directly.

---

## 📁 **MODULE LOCATIONS**

### ✅ **Correct Structure:**

```
backend/quantix_core/
├── learning/
│   └── primitives/
│       ├── __init__.py
│       └── structure.py              ← ONLY THIS FILE
│
├── engine/
│   └── primitives/
│       ├── __init__.py               ← Re-exports StructurePrimitive
│       ├── swing_detector.py         ← Runtime logic
│       ├── structure_events.py       ← Runtime logic
│       ├── evidence_scorer.py        ← Runtime logic
│       ├── fake_breakout_filter.py   ← Runtime logic
│       └── state_resolver.py         ← Runtime logic
│
└── api/
    └── routes/
        ├── features.py               ← Uses engine layer
        ├── structure.py              ← Uses engine layer
        ├── public.py                 ← Uses engine layer
        └── lab.py                    ← Uses engine layer
```

---

## 🚫 **FORBIDDEN PATTERNS**

### ❌ **Pattern 1: Direct Learning Import in API**

```python
# ❌ WRONG
from quantix_core.learning.primitives.structure import StructurePrimitive

# ✅ CORRECT
from quantix_core.engine.primitives import StructurePrimitive
```

### ❌ **Pattern 2: Cross-Module Confusion**

```python
# ❌ WRONG (swing_detector is NOT in learning)
from quantix_core.learning.primitives.swing_detector import SwingPoint

# ✅ CORRECT
from quantix_core.engine.primitives.swing_detector import SwingPoint
```

### ❌ **Pattern 3: Missing Data Source**

```python
# ❌ WRONG (yahoo_fetcher doesn't exist)
from quantix_core.ingestion.yahoo_fetcher import YahooFinanceFetcher

# ✅ CORRECT (Quantix uses Dukascopy)
from quantix_core.ingestion.dukascopy.fetcher import DukascopyFetcher
```

---

## ✅ **CORRECT IMPORT EXAMPLES**

### **Example 1: API Route Using Engine**

```python
# api/routes/structure.py
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.engine.primitives import StructurePrimitive  # Re-exported

router = APIRouter()
engine = StructureEngineV1()
```

### **Example 2: Engine Using Primitives**

```python
# engine/structure_engine_v1.py
from quantix_core.learning.primitives.structure import StructurePrimitive
from quantix_core.engine.primitives.swing_detector import SwingPoint
from quantix_core.engine.primitives.structure_events import StructureEvent

class StructureEngineV1:
    def __init__(self):
        self.structure_calc = StructurePrimitive()
```

### **Example 3: Engine Primitives __init__.py**

```python
# engine/primitives/__init__.py
from quantix_core.learning.primitives.structure import StructurePrimitive

__all__ = ['StructurePrimitive']
```

---

## 🔍 **VERIFICATION CHECKLIST**

Before committing, verify:

- [ ] No `from quantix_core.learning.primitives.swing_detector`
- [ ] No `from quantix_core.learning.primitives.structure_events`
- [ ] No `from quantix_core.ingestion.yahoo_fetcher`
- [ ] API routes import from `engine`, not `learning`
- [ ] `learning.primitives` contains ONLY `structure.py`
- [ ] `engine.primitives` contains runtime logic files

---

## 🚨 **ENFORCEMENT**

### **Pre-Commit Check:**

```bash
# Run this before committing
python scripts/check_imports.py
```

### **CI/CD Pipeline:**

```yaml
# .github/workflows/import-check.yml
- name: Verify Import Architecture
  run: python scripts/check_imports.py --strict
```

### **PR Review:**

❌ **Auto-reject if:**
- Imports from `learning.primitives` in `api.routes`
- Imports non-existent modules (`yahoo_fetcher`)
- Cross-module confusion (`swing_detector` from `learning`)

---

## 📝 **MIGRATION NOTES**

### **What Changed (2026-01-15):**

1. **Removed:** `yahoo_fetcher` module (never existed)
2. **Clarified:** `learning.primitives` = ONLY `structure.py`
3. **Clarified:** `engine.primitives` = runtime logic
4. **Fixed:** All cross-module import errors

### **Breaking Changes:**

- ❌ `YahooFinanceFetcher` removed (use Dukascopy)
- ❌ Direct `learning` imports in API routes forbidden
- ✅ Must use `engine` layer for API access

---

## 🎯 **SUMMARY**

| Module | Purpose | Imports From |
|--------|---------|--------------|
| `learning.primitives` | ML/Learning (structure only) | - |
| `engine.primitives` | Runtime logic | `learning.primitives.structure` |
| `api.routes` | API endpoints | `engine` (not `learning`) |
| `ingestion` | Data sources | Dukascopy (not Yahoo) |

---

**⛔ VIOLATIONS = FAILED PR**  
**✅ FOLLOW THIS = SMOOTH DEPLOYMENT**
