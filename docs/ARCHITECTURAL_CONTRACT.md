# 🛡️ SYSTEM ARCHITECTURE CONTRACT (INVIOLABLE)

**Checkpoint Date:** 2026-01-15  
**Status:** ACTIVE & ENFORCED

This document defines the **inviolable rules** for the Quantix AI Core architecture. These rules are "Checkpoints" that must NEVER be regressed or broken effectively known as "Rule Zero".

---

## 🚫 1. BACKEND: NO BLOCKING OPERATIONS
> **Rule:** Never initialize heavy engines, models, or network fetchers at the module level or within a synchronous HTTP request path.

- **Forbidden:** `engine = StructureEngine()` at top of file.
- **Forbidden:** `fetcher.fetch()` inside a `def get_endpoint():`.
- **Enforcement:** All endpoints must return within **<50ms**. Heavy compute belongs in Async Workers only.

## 🚫 2. DATA: NO REAL-TIME BLOCKING FETCH
> **Rule:** Never fetch live market data (OHLCV) directly within a user-facing API request.

- **Forbidden:** Calling Dukascopy/YahooFinance APIs while the user waits.
- **Required:** Background ingestion jobs write to DB/Cache; API reads from DB/Cache.

## 🚫 3. FRONTEND: ZERO DEPENDENCY LOADING
> **Rule:** The UI must never freeze or hang whilst waiting for the Backend.

- **Forbidden:** Indefinite open-ended `await fetch()`.
- **Required:** All fetches must have a strict **Timeout** (e.g., 5-10s) using `AbortController`.
- **Required:** `setLoading(false)` must always execute in a `finally` block or error handler.

## ✅ 4. FALLBACK: ALWAYS RENDER
> **Rule:** The UI must be usable even if the Backend is completely dead (502/503).

- **Required:** Graceful error states (e.g., "System Offline", "Using Cached Data").
- **Required:** Deterministic Mock/Snapshot data for critical demos/previews (like `/lab`) to ensure the page always renders something meaningful.

---

## 🔒 COMMITMENT
Any code changes that violate these rules will be rejected during review. This contract ensures the stability and responsiveness of the Quantix AI Core platform.
