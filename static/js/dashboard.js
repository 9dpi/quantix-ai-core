/**
 * Quantix AI Core - Dashboard Management
 * Handles Real-time Signals and Neural Intelligence
 */

const DASHBOARD = {
    async init() {
        console.log('🎯 Sniper Alerts System Initialized');
        this.renderDetailedSignals();

        document.addEventListener('data-refreshed', (e) => {
            console.log('🔄 Dashboard Data Synced');
        });
    },

    renderDetailedSignals() {
        const container = document.getElementById('signal-container');
        if (!container) return;

        const trades = [
            {
                asset: 'EUR/USD',
                direction: 'BUY',
                isBuy: true,
                timeframe: '15-Minute (M15)',
                session: 'London → New York Overlap',
                entry: '1.16710 – 1.16750',
                tp: '1.17080',
                sl: '1.16480',
                target: '+35 pips',
                rr: '1 : 1.40',
                suggestedRisk: '0.5% – 1%',
                tradeType: 'Intraday',
                confidence: '96%',
                posted: 'Jan 13, 2026 — 11:11 UTC'
            }
        ];

        container.innerHTML = trades.map(t => `
            <div class="alert-card-detailed">
                <div class="alert-header">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 800; font-size: 0.9rem;">📊 Asset: ${t.asset}</span>
                        <div class="dot dot-online" style="width: 8px; height: 8px;"></div>
                    </div>
                    <div style="font-weight: 700; color: ${t.isBuy ? 'var(--highlight)' : 'var(--warning)'}; font-size: 0.85rem;">
                        📌 Trade: ${t.isBuy ? '🟢 BUY' : '🔴 SELL'} (expect price to go ${t.isBuy ? 'up' : 'down'})
                    </div>
                </div>

                <div class="alert-section">
                    <div class="alert-section-title">Context</div>
                    <div style="font-size: 0.75rem;">⏳ Timeframe: ${t.timeframe}</div>
                    <div style="font-size: 0.75rem;">🌍 Session: ${t.session}</div>
                </div>

                <div class="alert-section">
                    <div class="alert-section-title">💰 Price Levels</div>
                    <div class="price-level"><span>Entry Zone:</span> <span>${t.entry}</span></div>
                    <div class="price-level" style="color: var(--highlight);"><span>Take Profit (TP):</span> <span>${t.tp}</span></div>
                    <div class="price-level" style="color: var(--warning);"><span>Stop Loss (SL):</span> <span>${t.sl}</span></div>
                </div>

                <div class="alert-section">
                    <div class="alert-section-title">📏 Trade Details</div>
                    <div class="price-level"><span>Target:</span> <span>${t.target}</span></div>
                    <div class="price-level"><span>Risk–Reward:</span> <span>${t.rr}</span></div>
                    <div class="price-level"><span>Suggested Risk:</span> <span>${t.suggestedRisk}</span></div>
                </div>

                <div class="alert-section" style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 4px;">
                    <div style="font-size: 0.75rem;">🕒 Type: ${t.tradeType}</div>
                    <div style="font-size: 0.75rem; font-weight: 700;">🧠 AI Confidence: <span style="color: var(--accent);">${t.confidence} ⭐</span></div>
                </div>

                <div style="font-size: 0.6rem; color: var(--text-dim); margin-top: 15px; border-top: 1px solid var(--border); padding-top: 10px;">
                    ⏰ Posted: ${t.posted}
                </div>

                <div style="margin-top: 12px; font-size: 0.6rem; color: var(--text-dim); font-style: italic;">
                    <div style="font-weight: 700; margin-bottom: 4px; color: var(--accent);">⏳ Auto-Expiry Rules:</div>
                    • Valid for this session only<br>
                    • Expires at NY close or if TP/SL hit<br>
                    • No entry if price moved significantly
                </div>
            </div>
        `).join('');
    }
};

// Start
document.addEventListener('DOMContentLoaded', () => DASHBOARD.init());
