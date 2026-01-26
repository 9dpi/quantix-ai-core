/**
 * Quantix AI Core - Signal Engine Lab (Experimental)
 * Snapshot-based logic for Market References.
 * 
 * v2.0 - Robust / Defensive / Async-Safe
 */

const SIGNALS = {
    isLoading: false,

    async init() {
        console.log('🧪 Signal Engine Lab Initializing...');

        // ✅ FIX 1: Always fetch on load
        await this.loadReferences();

        // ✅ FIX 2: Refetch on visibility change (Tab Switch / Return)
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === "visible") {
                console.log('👀 Tab visible - refreshing signals...');
                this.loadReferences();
            }
        });
    },

    async loadReferences() {
        if (this.isLoading) return;
        this.isLoading = true;

        const container = document.getElementById('signals-container');
        const syncLabel = document.getElementById('last-sync-time');

        // Set Loading State
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 100px; color: var(--text-dim);">
                <div class="pulse-small" style="margin: 0 auto 20px;"></div>
                <div style="font-size: 0.9rem;">Connecting to Quantix Lab Engine...</div>
            </div>
        `;

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/latest-lab?_=${Date.now()}`);

            if (!response.ok) throw new Error(`API Error: ${response.status}`);

            const results = await response.json();
            container.innerHTML = '';

            if (results && results.length > 0) {
                results.forEach(data => this.renderLabCard(container, data));
                if (syncLabel) syncLabel.innerText = `Last update: ${new Date().toLocaleTimeString()} UTC`;
            } else {
                this.renderEmptyState(container);
            }

        } catch (e) {
            console.error("🔥 Signals Load Failed:", e);
            this.renderEmptyState(container);
        } finally {
            this.isLoading = false;
        }
    },

    renderLabCard(container, data) {
        const bias = data.direction || "WAIT";
        const confidence = data.ai_confidence || 0;
        const asset = data.asset || "EURUSD";
        const timeframe = data.timeframe || "M15";

        const card = document.createElement('div');
        card.className = 'reference-card';

        // Dynamic Styling
        const isBuy = bias === 'BUY';
        const accentColor = isBuy ? 'var(--highlight)' : (bias === 'SELL' ? '#ef4444' : 'var(--text-dim)');
        const icon = isBuy ? "🟢" : (bias === 'SELL' ? "🔴" : "✋");

        const entryLow = parseFloat(data.entry_low || 0).toFixed(5);
        const entryHigh = parseFloat(data.entry_high || data.entry_low || 0).toFixed(5);
        const tp = parseFloat(data.tp || 0).toFixed(5);
        const sl = parseFloat(data.sl || 0).toFixed(5);

        const genTime = data.generated_at ? new Date(data.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now';

        card.innerHTML = `
            <div style="position: absolute; top: 12px; left: 12px; display: flex; gap: 6px;">
                 <span style="font-size: 0.5rem; background: rgba(255,255,255,0.05); color: var(--text-dim); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--border);">LAB_CANDIDATE</span>
            </div>

            <div class="card-badge" style="background: rgba(0,0,0,0.3); border: 1px solid ${accentColor}; color: ${accentColor}; top: 24px;">
                ${bias}
            </div>
            
            <div class="symbol-title" style="margin-top: 10px;">${asset}</div>
            <span class="timeframe-label">⏳ ${timeframe} • Live Analysis</span>
            
            <div style="margin: 20px 0;">
                <div style="font-size: 0.9rem; font-weight: 800; color: ${accentColor}; margin-bottom: 4px;">
                    ${icon} AI Bias: ${confidence > 0.75 ? 'Strong' : 'Evaluating'}
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="confidence-meter" style="height: 4px; background: rgba(255,255,255,0.1);">
                        <div class="confidence-fill" style="width: ${Math.min(confidence * 100, 100)}%; height: 100%; background: ${accentColor}; border-radius: 100px;"></div>
                    </div>
                    <span style="font-size: 0.7rem; font-weight: 700;">${(confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="level-grid" style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 12px; border: 1px solid var(--border); display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="grid-column: 1 / -1; margin-bottom: 12px;">
                    <div class="level-label" style="font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase;">💰 Entry Zone</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; font-size: 1rem; color: var(--text-main);">${entryLow} — ${entryHigh}</div>
                </div>
                <div>
                    <div class="level-label" style="font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase;">🎯 Target (TP)</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; color: var(--highlight);">${tp}</div>
                </div>
                <div style="text-align: right;">
                    <div class="level-label" style="font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase;">🛑 Protect (SL)</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; color: #ef4444;">${sl}</div>
                </div>
            </div>

            <div class="meta-footer" style="margin-top: 20px; font-size: 0.6rem; display: flex; justify-content: space-between; color: var(--text-dim); border-top: 1px solid var(--border); padding-top: 10px;">
                <div>T0 CANDIDATE | Gen: ${genTime} UTC</div>
                <div style="font-weight: 700; color: var(--accent);">STRETEGY: V1 ALPHA</div>
            </div>
        `;

        container.appendChild(card);
    },

    renderErrorCard(container, assetName) {
        const div = document.createElement('div');
        div.className = 'reference-card';
        div.style.borderColor = 'var(--warning)';
        div.innerHTML = `
            <div style="color: var(--warning); font-weight: bold;">⚠️ ${assetName} Data Error</div>
            <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 8px;">Could not render signal data. Source returned invalid format.</div>
        `;
        container.appendChild(div);
    },

    renderEmptyState(container) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-dim);">
                <h3>💤 No Signals Generated</h3>
                <p>The signal engine is online but returned no data. Try again shortly.</p>
                <button onclick="SIGNALS.loadReferences()" class="btn-primary" style="margin-top: 16px;">Refresh</button>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => SIGNALS.init());
