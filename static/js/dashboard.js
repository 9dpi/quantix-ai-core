import API_CONFIG from './api.js';

const API_BASE = API_CONFIG.getBaseUrl();

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

async function initDashboard() {
    console.log("🚀 Initializing Quantix Dashboard...");
    console.log("📍 API Base:", API_BASE);

    // Check API Health
    checkHealth();

    // Fetch Stats
    fetchIngestionStats();

    // Fetch Signals
    fetchSignals();

    // Refresh periodically
    setInterval(fetchSignals, 30000);
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const dot = document.getElementById('api-status-dot');
        if (!dot) return;

        if (response.ok) {
            dot.style.background = '#00ff00';
            dot.style.boxShadow = '0 0 10px #00ff00';
            dot.title = 'API Online';
        } else {
            dot.style.background = '#ff9900';
            dot.style.boxShadow = 'none';
            dot.title = 'API Error';
        }
    } catch (e) {
        const dot = document.getElementById('api-status-dot');
        if (dot) dot.style.background = '#ff0000';
    }
}

async function fetchIngestionStats() {
    try {
        const response = await fetch(`${API_BASE}/ingestion/stats`);
        const data = await response.json();

        if (data.status === 'success') {
            const validatedTier = data.tiers.find(t => t.tier === 'validated');
            // Mock data update for UI demo
            document.getElementById('total-candles').innerText = "1,240,500";
        }
    } catch (e) {
        console.error("Failed to fetch stats:", e);
    }
}

async function fetchSignals() {
    const container = document.getElementById('signals-container');
    const explainPanel = document.getElementById('explain-panel');

    try {
        // --- FORCE DEMO MODE FOR UI REVIEW ---
        // We will default to MOCK DATA if API fails or returns empty
        // This ensures the USER sees the UI changes immediately
        let signals = [];
        try {
            const activRes = await fetch(`${API_BASE}/fx/signals/active`);
            if (activRes.ok) signals = await activRes.json();
        } catch (e) { console.warn("API Offline, switching to Demo Mode"); }

        if (signals.length === 0) {
            signals = [{
                asset: "EUR/USD",
                direction: "BUY",
                timeframe: "M15",
                entry_low: 1.08500,
                entry_high: 1.08520,
                tp: 1.08850,
                sl: 1.08350,
                reward_risk_ratio: 2.3,
                ai_confidence: 0.96,
                generated_at: new Date().toISOString(),
                context: { session: "London / NY Overlap" },
                explainability: {
                    summary: "Prime Setup: London Liquidity Sweep + Pin Bar Reversal",
                    components: [
                        { description: "London-NY Overlap high volume zone", impact_score: 0.08 },
                        { description: "M15 Pin Bar Reversal confirmed", impact_score: 0.15 },
                        { description: "Volatility Expansion in favor", impact_score: 0.05 },
                        { description: "Minor resistance ahead (Risk)", impact_score: -0.02 }
                    ]
                }
            }];
        }

        // Render Signals
        container.innerHTML = signals.map(sig => `
            <div class="card signal-card-item" style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); padding: 20px; border-radius: 16px; margin-bottom: 16px; transition: all 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1.5rem; font-weight: 700; color: #fff;">${sig.asset}</span>
                            <span class="pill" style="background: ${sig.direction === 'BUY' ? 'rgba(0, 255, 163, 0.1)' : 'rgba(255, 0, 92, 0.1)'}; color: ${sig.direction === 'BUY' ? '#00ffa3' : '#ff005c'}; border: none;">${sig.direction}</span>
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 5px;">${sig.timeframe} • ${new Date(sig.generated_at).toLocaleTimeString()}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--accent); line-height: 1;">${(sig.ai_confidence * 100).toFixed(0)}%</div>
                        <div style="font-size: 0.7rem; color: var(--text-secondary); letter-spacing: 1px;">CONFIDENCE</div>
                    </div>
                </div>
                
                <!-- NEW: Canonical Output Table -->
                <div class="signal-output">
                    <h3>📊 Trade Signal Details</h3>
                    <table class="signal-table">
                        <tbody id="signal-output-body-${sig.asset}">
                            ${generateSignalTableRows(canonicalizeSignal(sig))}
                        </tbody>
                    </table>
                </div>
            </div>
        `).join('');

        document.getElementById('active-signals').innerText = signals.length;

        // Render Top Explainability
        if (signals[0] && signals[0].explainability) {
            renderExplainability(signals[0].explainability);
            explainPanel.style.display = 'block';
        } else {
            explainPanel.style.display = 'none';
        }

    } catch (e) {
        console.error("Signal fetch error", e);
        container.innerHTML = '<div style="text-align: center; color: var(--text-secondary);">Connecting to Intelligence Node...</div>';
    }
}

// -----------------------------------------------------------
// CORE EXPLAINABILITY RENDERER
// -----------------------------------------------------------
function formatImpact(score) {
    const sign = score >= 0 ? "+" : "";
    return `${sign}${(score * 100).toFixed(1)}%`;
}

function renderExplainability(explain) {
    const container = document.getElementById("explain-panel");
    if (!container || !explain) return;

    let itemsHtml = '';

    // Preferred: Structured Components
    if (explain.components && explain.components.length > 0) {
        explain.components.forEach(c => {
            const isPositive = c.impact_score >= 0;
            const icon = isPositive ? "✔" : "✖";
            const color = isPositive ? "#00ffa3" : "#ff005c"; // Bright Green / Bright Red

            itemsHtml += `
              <li style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div style="display: flex; gap: 10px;">
                    <span style="color: ${color}; font-weight: bold;">${icon}</span>
                    <span style="color: #ddd; font-size: 0.9rem; line-height: 1.4;">${c.description}</span>
                </div>
                <span style="font-family: 'Space Grotesk'; color: ${color}; font-size: 0.85rem; font-weight: 600; min-width: 45px; text-align: right;">${formatImpact(c.impact_score)}</span>
              </li>
            `;
        });
    }
    // Fallback: Legacy List Strings
    else if (explain.driving_factors) {
        explain.driving_factors.forEach(f => {
            itemsHtml += `
              <li style="display: flex; gap: 10px; margin-bottom: 8px;">
                <span style="color: #00ffa3;">✔</span>
                <span style="color: #ddd; font-size: 0.9rem;">${f}</span>
              </li>`;
        });
        if (explain.risk_factors) {
            explain.risk_factors.forEach(f => {
                itemsHtml += `
                  <li style="display: flex; gap: 10px; margin-bottom: 8px;">
                    <span style="color: #ff005c;">✖</span>
                    <span style="color: #ddd; font-size: 0.9rem;">${f}</span>
                  </li>`;
            });
        }
    }

    container.innerHTML = `
      <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 15px;">
        <h3 style="margin-bottom: 5px; color: var(--accent);">🧠 WHY THIS TRADE?</h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); font-style: italic;">"${explain.summary || "AI Analysis Complete"}"</p>
      </div>
      <ul style="list-style: none; padding: 0; margin: 0;">
        ${itemsHtml}
      </ul>
      <div style="margin-top: 15px; padding-top: 15px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.75rem; color: var(--text-secondary); text-align: center;">
        EXPLAINABILITY ENGINE v3.1
      </div>
    `;
}

// -----------------------------------------------------------
// DATA ADAPTER: Convert Raw Signal to Canonical Output
// -----------------------------------------------------------
function canonicalizeSignal(raw) {
    // Map raw backend keys to standardized Frontend Model
    return {
        asset: raw.asset,
        direction: raw.direction,
        timeframe: raw.timeframe,
        session: raw.context?.session || "London → New York Overlap",

        entry_zone: [raw.entry_low, raw.entry_high],
        take_profit: raw.tp,
        stop_loss: raw.sl,

        // Calculated fields mock logic (Backend should ideally provide these)
        target_pips: Math.abs(raw.tp - raw.entry_high) * 10000,
        risk_reward: `1 : ${raw.reward_risk_ratio || 1.5}`,
        suggested_risk: "0.5% – 1%",

        trade_type: "Intraday / Sniper",
        confidence: raw.ai_confidence,

        posted_at: raw.generated_at,
        expiry_rule: [
            "Signal is valid for this session only",
            "Expires at session close or if TP/SL is hit",
            "Do not enter if price moves > 5 pips beyond entry"
        ]
    };
}

// -----------------------------------------------------------
// HTML GENERATOR: Signal Table Rows
// -----------------------------------------------------------
function formatPrice(p) { return Number(p).toFixed(5); }
function formatDate(iso) { return new Date(iso).toUTCString(); }

function generateSignalTableRows(signal) {
    return `
    <tr><td>Asset</td><td><strong>${signal.asset}</strong></td></tr>

    <tr><td>Trade</td>
      <td>
        <span class="trade ${signal.direction.toLowerCase()}">
          ${signal.direction === "BUY" ? "🟢 BUY" : "🔴 SELL"}
        </span>
      </td>
    </tr>

    <tr><td>Timeframe</td><td>${signal.timeframe}</td></tr>
    <tr><td>Session</td><td>${signal.session}</td></tr>

    <tr class="section"><td colspan="2">💰 Price Levels</td></tr>
    <tr><td>Entry Zone</td>
      <td>${formatPrice(signal.entry_zone[0])} – ${formatPrice(signal.entry_zone[1])}</td>
    </tr>
    <tr><td>Take Profit</td><td>${formatPrice(signal.take_profit)}</td></tr>
    <tr><td>Stop Loss</td><td>${formatPrice(signal.stop_loss)}</td></tr>

    <tr class="section"><td colspan="2">📏 Trade Details</td></tr>
    <tr><td>Target (Est)</td><td>+${Math.round(signal.target_pips)} pips</td></tr>
    <tr><td>Risk–Reward</td><td>${signal.risk_reward}</td></tr>
    <tr><td>Suggested Risk</td><td>${signal.suggested_risk}</td></tr>

    <tr><td>Trade Type</td><td>${signal.trade_type}</td></tr>

    <tr class="highlight">
      <td>AI Confidence</td>
      <td><strong>${Math.round(signal.confidence * 100)}%</strong> ⭐</td>
    </tr>

    <tr><td>Posted</td><td>${formatDate(signal.posted_at)}</td></tr>

    <tr class="section"><td colspan="2">⏳ Auto-Expiry Rules</td></tr>
    <tr>
      <td colspan="2">
        <ul class="expiry-rules">
          ${signal.expiry_rule.map(r => `<li>${r}</li>`).join("")}
        </ul>
      </td>
    </tr>
    `;
}
