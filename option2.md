Use Binance/Another Feed For Logic, Accept Minor Drift

Many signal platforms:
	•	Use Binance API for price logic
	•	Users execute on their own broker
	•	Accept slight entry differences

This works if:
	•	SL/TP buffer is reasonable
	•	Strategy is not ultra tight scalping

⸻

❌ What NOT To Do

Do not try to:

“Make it match TradingView candle by candle”

That will waste time and never be perfect.

⸻

🧠 Now Let’s Talk Practical Validation

Your dev’s system should:

For each signal:
	1.	Store:
	•	Entry price
	•	SL
	•	TP
	•	Time issued
	2.	Pull 1m or 5m candle data continuously
	3.	Check:

BUY logic:
	•	Entry triggered if high >= entry
	•	TP if high >= tp
	•	SL if low <= sl

SELL logic:
	•	Entry if low <= entry
	•	TP if low <= tp
	•	SL if high >= sl

	4.	Record which occurred first.

This must be done using a single consistent feed.

⸻

⚠️ Spread Matters

EURUSD:
	•	Pepperstone Razor spread might be 0.1–0.3 pips
	•	If your backend uses mid-price,
SL/TP hits may differ slightly

Professional approach:
	•	Add spread buffer
	•	Or validate using bid/ask instead of midpoint

⸻

🔥 Serious Question Now

What type of system are you building?

A) Scalping (5–10 pip SL)
B) Intraday (15–40 pip SL)
C) Swing (50+ pip SL)

If it’s scalping,
data precision matters massively.

If it’s intraday,
minor feed differences won’t matter much.