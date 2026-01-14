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
        // In real backend, signals endpoint should return list
        // For Phase 3.1 demo, we'll hit generate to create a fresh one if list is empty
        let signals = [];
        try {
            const activRes = await fetch(`${API_BASE}/fx/signals/active`);
            if (activRes.ok) signals = await activRes.json();
        } catch (e) { }

        if (signals.length === 0) {
            // Auto-generate one for demo purposes (Internal Alpha specific behavior)
            const genRes = await fetch(`${API_BASE}/fx/signals/generate?asset=EURUSD&timeframe=M15`, { method: 'POST' });
            if (genRes.ok) signals = [await genRes.json()];
        }

        if (signals.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">Waiting for market structure...</div>';
            return;
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
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px;">
                    <div>
                        <div style="font-size: 0.7rem; color: #888;">ENTRY</div>
                        <div style="font-family: 'Space Grotesk'; font-weight: 600;">${sig.entry_low}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: #00ffa3;">TP</div>
                        <div style="font-family: 'Space Grotesk'; font-weight: 600;">${sig.tp}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: #ff005c;">SL</div>
                        <div style="font-family: 'Space Grotesk'; font-weight: 600;">${sig.sl}</div>
                    </div>
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

    // Determine driving vs risks logic if needed, or use simple list
    // Backend V3.1 returns: driving_factors (list of strings) OR components (list of objects)
    // We handle both for robustness

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
