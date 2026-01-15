# 🗺️ QUANTIX AI CORE - INFORMATION ARCHITECTURE (IA)

**Status:** ✅ IMPLEMENTED & FROZEN  
**Target Architecture:** 4-Core Unified System

---

## 🏗️ **SITE MAP**

### 1. `/` (About)
- **Role:** Landing / Positioning / Marketing.
- **Audience:** Investors, Partners, New Users.
- **Content:** What Quantix is, High-level USPs (Deterministic, Audit-ready).

### 2. `/dashboard/` (Live System)
- **Role:** THE SHOWCASE / MISSION CONTROL.
- **Audience:** Real-time observers, Portfolio Managers.
- **Integrated Sections:**
    - 📊 **Market State Reasoning:** Live Engine Output (EURUSD, confidence, etc).
    - 🛰️ **Infrastructure Health:** (Merged from old /status) Data ingestion, Gateway, DB node.
    - 🚀 **Deployment Telemetry:** Railway status, Build hashes, Latency (ms).
    - ⚖️ **Data Governance:** Dukascopy feed rules, OHLC integrity.
    - 🧪 **Capabilities:** Supported timeframes and symbols.

### 3. `/reasoning/` (The "How")
- **Role:** TRANSPARENCY / ANTI-BLACK-BOX.
- **Audience:** Technical Partners, Quants, Due Diligence.
- **Content:** Primitive definitions, structure logic details, evidence scoring explanation.

### 4. `/api/` (Developer Portal)
- **Role:** INTEGRATION / INFRASTRUCTURE.
- **Audience:** Developers, Quantitative Researchers.
- **Content:** Documentation, Rate limits, Authorization headers, Live Railway mapping.

### 5. `/disclaimer/` (Legal)
- **Role:** RISK SHIELD.
- **Content:** Mandatory legal notice, No-financial-advice clause.

---

## 🧠 **DESIGN PRINCIPLES**

1. **Unified Dashboard:** Status is NOT a separate concern; it is a core capability of a live system.
2. **Deterministic UI:** No "buy/sell" buttons. Everything is "State" and "Evidence".
3. **Transparency First:** Build hashes and Trace IDs are visible to prove accountability.
4. **Latency Honesty:** Explicitly state data latency (5-10m) to manage expectations.

---

## 🔄 **MIGRATION NOTES**

- `status/index.html` is now a **Redirector** to `/dashboard/`.
- All Global Nav Bars have been updated to the 4-core structure.
- `dashboard.js` now handles both Analysis and Infrastructure telemetry.

---

**Archived Version:** 1.4  
**Last Update:** 2026-01-15 09:40 UTC  
**By:** Antigravity AI
