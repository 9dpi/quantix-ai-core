/**
 * Quantix AI Core - Signal Engine Lab (Experimental)
 * Snapshot-based logic for Market References.
 */

const SIGNALS = {
    async init() {
        console.log('🧪 Signal Engine Lab Initializing...');
        await this.loadReferences();
    },

    async loadReferences() {
        const container = document.getElementById('signals-container');
        const syncLabel = document.getElementById('last-sync-time');
        const symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"];

        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 100px; color: var(--text-dim);">
                <div class="pulse-small" style="margin: 0 auto 20px;"></div>
                Generating Intelligence Snapshots...
            </div>
        `;

        const results = [];
        for (const symbol of symbols) {
            const data = await this.fetchLabSnapshot(symbol, "H4");
            if (data) results.push(data);
        }

        container.innerHTML = '';
        if (results.length > 0) {
            results.forEach(data => this.renderLabCard(container, data));
            syncLabel.innerText = `Last snapshot: ${new Date().toLocaleTimeString()} UTC`;
        } else {
            container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--warning);">Laboratory Engine Offline. Check System Status.</div>';
        }
    },

    async fetchLabSnapshot(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/lab/market-reference?symbol=${symbol}&tf=${tf}`);
            if (!response.ok) return null;
            return await response.json();
        } catch (e) {
            console.error(`❌ Lab fetch failed for ${symbol}:`, e);
            return null;
        }
    },

    renderLabCard(container, data) {
        const card = document.createElement('div');
        const bias = data.trade_bias;
        const strength = data.bias_strength;
        const isNeutral = bias === 'NEUTRAL';

        card.className = 'reference-card';

        // Colors
        let accentColor = "var(--text-dim)";
        let biasIcon = "⚪";
        if (bias === 'BUY') { accentColor = "var(--highlight)"; biasIcon = "🟢"; }
        if (bias === 'SELL') { accentColor = "#ef4444"; biasIcon = "🔴"; }

        card.innerHTML = `
            <div style="position: absolute; top: 12px; left: 12px; display: flex; gap: 6px;">
                 <span style="font-size: 0.5rem; background: rgba(255,165,0,0.2); color: orange; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,165,0,0.3);">SNAPSHOT</span>
                 <span style="font-size: 0.5rem; background: rgba(56,189,248,0.1); color: var(--accent); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--accent);">AUTO-EXPIRING</span>
            </div>

            <div class="card-badge" style="background: ${isNeutral ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.3)'}; border: 1px solid ${accentColor}; color: ${accentColor}; top: 24px;">
                ${bias} ${strength !== 'N/A' ? `(${strength})` : ''}
            </div>
            
            <div class="symbol-title" style="margin-top: 10px;">${data.asset}</div>
            <span class="timeframe-label">⏳ ${data.timeframe} • ${data.session}</span>
            
            <div style="margin: 20px 0;">
                <div style="font-size: 0.9rem; font-weight: 800; color: ${accentColor}; margin-bottom: 4px;">
                    ${biasIcon} Trade Bias: ${bias}
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="confidence-meter" style="height: 4px;">
                        <div class="confidence-fill" style="width: ${data.confidence * 100}%; background: ${accentColor}"></div>
                    </div>
                    <span style="font-size: 0.7rem; font-weight: 700;">${(data.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="level-grid" style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div class="level-item" style="grid-column: 1 / -1; background: transparent; border: none; padding: 0; margin-bottom: 12px;">
                    <div class="level-label">💰 Entry Zone</div>
                    <div class="level-value" style="font-size: 1.1rem; color: var(--text-main);">${data.price_levels.entry_zone[0]} — ${data.price_levels.entry_zone[1]}</div>
                </div>
                <div class="level-item" style="background: transparent; border: none; padding: 0;">
                    <div class="level-label">🎯 Take Profit</div>
                    <div class="level-value" style="color: var(--highlight);">${data.price_levels.take_profit}</div>
                </div>
                <div class="level-item" style="background: transparent; border: none; padding: 0; text-align: right;">
                    <div class="level-label">🛑 Stop Loss</div>
                    <div class="level-value" style="color: #ef4444;">${data.price_levels.stop_loss}</div>
                </div>
            </div>

            <div style="margin: 20px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.75rem;">
                <div style="color: var(--text-dim);">Target: <span style="color: var(--text-main); font-weight: 700;">+${data.trade_details.target_pips} pips</span></div>
                <div style="color: var(--text-dim); text-align: right;">R:R Ratio: <span style="color: var(--text-main); font-weight: 700;">1:${data.trade_details.risk_reward}</span></div>
                <div style="color: var(--text-dim);">Sugg. Risk: <span style="color: var(--text-main); font-weight: 700;">0.5% - 1%</span></div>
                <div style="color: var(--text-dim); text-align: right;">Type: <span style="color: var(--text-main); font-weight: 700;">${data.trade_details.trade_type}</span></div>
            </div>
            
            <div class="meta-footer" style="margin-top: 10px; font-size: 0.6rem;">
                <div>⏰ Generated: ${new Date(data.meta.generated_at).toLocaleTimeString()} UTC</div>
                <div>⏳ Expires: NY Close</div>
            </div>
        `;

        container.appendChild(card);
    }
};

document.addEventListener('DOMContentLoaded', () => SIGNALS.init());
