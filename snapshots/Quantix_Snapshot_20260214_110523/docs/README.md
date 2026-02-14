# Quantix AI Core - Forex Signal Intelligence Engine

## 🎯 What This Is (And Isn't)

### ❌ NOT
- AI that predicts "price will go up/down"
- Magic indicator combination
- Get-rich-quick signal service

### ✅ YES
- **Probability-based trade setup generator**
- Market structure + session behavior analysis
- Conditional entry zones with invalidation rules
- Professional API for internal/external use

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Quantix AI Core Engine                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Market     │  │  Structure   │  │  Entry Zone  │      │
│  │   Context    │→ │  Liquidity   │→ │    Agent     │      │
│  │    Agent     │  │    Agent     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Risk     │  │ Probability  │  │   Expiry &   │      │
│  │ Construction │→ │  Confidence  │→ │ Invalidation │      │
│  │    Agent     │  │    Agent     │  │    Agent     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           ↓                                  │
│                  ┌─────────────────┐                        │
│                  │  Signal Output  │                        │
│                  │  (JSON Schema)  │                        │
│                  └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
                  ┌─────────────────┐
                  │   FastAPI       │
                  │   Endpoints     │
                  └─────────────────┘
                           ↓
                  ┌─────────────────┐
                  │   Supabase      │
                  │   Database      │
                  └─────────────────┘
```

---

## 📊 Signal Output Schema

```json
{
  "asset": "EURUSD",
  "direction": "BUY",
  "timeframe": "M15",
  "session": "LONDON_NY_OVERLAP",
  
  "entry_zone": [1.16710, 1.16750],
  "take_profit": 1.17080,
  "stop_loss": 1.16480,
  
  "pips_target": 35,
  "risk_reward": 1.40,
  "trade_type": "INTRADAY",
  
  "ai_confidence": 0.96,
  "confidence_grade": "A+",
  
  "model_version": "quantix_fx_v1.2",
  "generated_at": "2026-01-13T11:11:00Z",
  
  "expiry": {
    "type": "SESSION_BASED",
    "session_end": "NY_CLOSE",
    "invalidate_if": [
      "TP_HIT",
      "SL_HIT",
      "PRICE_BREAK_ENTRY_ZONE"
    ]
  }
}
```

---

## 🧠 AI Confidence Calculation

**NOT** a "feeling" - it's a mathematical probability:

```
AI_Confidence = 
  P(Structure Valid)      × 
  P(Session Favorable)    × 
  P(Volatility Normal)    × 
  P(Historical Similarity)
```

**Example:**
- Structure match: 0.98
- Session match: 0.97
- Volatility regime: 0.99
- Backtest win-rate: 0.99
→ **0.96 (96%)**

This represents: **Probability that price hits TP before SL under current session & regime**

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone and navigate
cd Quantix_AI_Core

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 2. Run Locally
```bash
# Start API server
uvicorn src.api.main:app --reload

# Generate a signal
curl -X POST http://localhost:8000/api/v1/fx/signal \
  -H "Content-Type: application/json" \
  -d '{"asset": "EURUSD", "timeframe": "M15"}'
```

### 3. Deploy to Railway
```bash
# Railway CLI
railway login
railway init
railway up
```

---

## 📁 Project Structure

```
Quantix_AI_Core/
├── src/
│   ├── agents/              # 6 AI Agents
│   │   ├── market_context.py
│   │   ├── structure_liquidity.py
│   │   ├── entry_zone.py
│   │   ├── risk_construction.py
│   │   ├── probability_confidence.py
│   │   └── expiry_invalidation.py
│   ├── api/                 # FastAPI
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── signals.py
│   │   │   └── health.py
│   │   └── middleware/
│   ├── database/            # Supabase
│   │   ├── models.py
│   │   ├── connection.py
│   │   └── migrations/
│   ├── schemas/             # Pydantic
│   │   ├── signal.py
│   │   └── market.py
│   └── utils/
│       ├── session_detector.py
│       └── validators.py
├── tests/
│   ├── unit/
│   └── integration/
├── config/
│   ├── settings.py
│   └── constants.py
├── docker/
│   └── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🔑 Key Features

### 1. Session-Aware Analysis
- Tokyo, London, NY sessions
- Overlap detection
- Liquidity window identification

### 2. Structure-Based Logic
- BOS/CHoCH detection
- Liquidity sweep identification
- Premium/Discount zones

### 3. Entry Zone (Not Point)
- FVG analysis
- Order Block detection
- VWAP deviation
- ±2 pips range

### 4. Smart Invalidation
- Auto-expire at session end
- Price breaks entry zone
- Volatility spike detection
- News event proximity

### 5. Probability-Based Confidence
- Mathematical calculation
- Backtest validation
- Historical pattern matching
- Legal protection (not prediction)

---

## 🛡️ Legal & Ethical

**This system does NOT:**
- Guarantee profits
- Predict future prices
- Provide financial advice

**This system DOES:**
- Analyze market structure
- Calculate setup probabilities
- Provide conditional trade zones
- Auto-invalidate when conditions change

**Disclaimer:** All signals are for informational purposes only. Users are responsible for their own trading decisions.

---

## 📈 Roadmap

- [x] Phase 1: Foundation & Schema
- [ ] Phase 2: AI Agents Implementation
- [ ] Phase 3: Database Layer
- [ ] Phase 4: API Development
- [ ] Phase 5: Testing & Validation
- [ ] Phase 6: Railway Deployment

---

## 🤝 Contributing

This is an internal project. For external API access, contact the development team.

---

## 📄 License

Proprietary - Quantix AI Core © 2026
