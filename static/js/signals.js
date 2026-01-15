/**
 * Quantix AI Core - Market Reference (Signals) Manager
 * Renders high-confidence structural references.
 */

const SIGNALS = {
    async init() {
        console.log('📡 Quantix Market Reference Engine Initializing...');
        await this.loadReferences();
    },

    async loadReferences() {
        const container = document.getElementById('signals-container');
        const symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"];

        container.innerHTML = ''; // Clear loading

        for (const symbol of symbols) {
            const data = await this.fetchReference(symbol, "H4");
            if (data) {
                this.renderCard(container, data);
            }
        }
    },

    async fetchReference(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/public/market-reference?symbol=${symbol}&tf=${tf}`);
            if (!response.ok) return null;
            return await response.json();
        } catch (e) {
            console.error(`❌ Failed to fetch reference for ${symbol}:`, e);
            return null;
        }
    },

    renderCard(container, data) {
        const card = document.createElement('div');
        const isBullish = data.bias.direction === 'bullish';
        card.className = 'reference-card';

        const confidence = (data.bias.confidence * 100).toFixed(1);

        card.innerHTML = `
            <div class="card-badge ${isBullish ? 'badge-bullish' : 'badge-bearish'}">
                ${data.bias.direction} Structure
            </div>
            
            <div class="symbol-title">${data.meta.symbol}</div>
            <span class="timeframe-label">Primary Timeframe: ${data.meta.timeframe}</span>
            
            <div class="bias-row">
                <div style="font-size: 0.65rem; font-weight: 700; color: var(--text-dim); min-width: 90px; text-transform: uppercase;">Confidence</div>
                <div class="confidence-meter">
                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                </div>
                <div style="font-size: 0.8rem; font-weight: 800; color: var(--accent);">${confidence}%</div>
            </div>
            
            <div class="level-grid">
                <div class="level-item" style="grid-column: 1 / -1; border-color: rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.02);">
                    <div class="level-label">Interest Zone (Reference)</div>
                    <div class="level-value">${data.price_levels.interest_zone.from} — ${data.price_levels.interest_zone.to}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Upper Ref Level</div>
                    <div class="level-value" style="color: var(--highlight);">${data.price_levels.structure_target}</div>
                </div>
                <div class="level-item">
                    <div class="level-label">Lower Invalidation</div>
                    <div class="level-value" style="color: #ef4444;">${data.price_levels.invalidation_level}</div>
                </div>
            </div>

            <div style="margin-bottom: 24px; padding: 12px; background: rgba(0,0,0,0.1); border-radius: 8px;">
                <div style="font-size: 0.65rem; color: var(--accent); font-weight: 800; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em;">Evidence Summary</div>
                <ul style="margin: 0; padding-left: 14px; font-size: 0.75rem; color: var(--text-dim); line-height: 1.5;">
                    <li>Higher-high / lower sequence intact</li>
                    <li>No confirmed structural invalidation</li>
                    <li>Dominant impulse > corrective moves</li>
                </ul>
            </div>

            <div style="margin-bottom: 24px;">
                <div style="font-size: 0.65rem; color: var(--text-dim); margin-bottom: 8px; text-transform: uppercase;">Structural Metrics</div>
                <div style="display: flex; gap: 24px; font-size: 0.8rem;">
                    <div><span style="color: var(--text-dim);">Proj:</span> ~${data.metrics.projected_move_pips} pips</div>
                    <div><span style="color: var(--text-dim);">RR:</span> ~1:${data.metrics.structure_rr}</div>
                </div>
            </div>
            
            <div class="meta-footer">
                <div class="timer-badge">
                    <div class="pulse-tiny"></div> Valid for ${this.getTimeRemaining(data.meta.expires_at)}
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;">SOURCE: DUKASCOPY</div>
            </div>
        `;

        container.appendChild(card);
    },

    getTimeRemaining(expiresAt) {
        const expiry = new Date(expiresAt);
        const now = new Date();
        const diffMs = expiry - now;

        if (diffMs <= 0) return "Expired";

        const hours = Math.floor(diffMs / 3600000);
        const mins = Math.floor((diffMs % 3600000) / 60000);

        return `${hours}h ${mins}m`;
    }
};

document.addEventListener('DOMContentLoaded', () => SIGNALS.init());
