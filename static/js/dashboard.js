/**
 * Quantix AI Core - Public Dashboard Manager
 * Implements 3-layer architecture: Core Analysis, Lab Support, and Status.
 */

const DASHBOARD = {
    async init() {
        console.log('🏛️ Quantix Public Dashboard Initializing...');
        await this.refreshContent();

        // Refresh every 2 minutes to match Miner cycle
        setInterval(() => this.refreshContent(), 120000);
    },

    async refreshContent() {
        const symbol = "EURUSD";
        const tf = "H4";

        try {
            // Layer 1: Core Research (Dukascopy Source)
            const startTime = performance.now();
            const coreData = await this.fetchCore(symbol, tf);
            const latency = Math.round(performance.now() - startTime);

            if (coreData) {
                this.updateCoreUI(coreData);
                this.updateTelemetry(latency);
            }

            // Layer 2: Live Signal Feed [T1 -> T2]
            const signalData = await this.fetchSignals();
            if (signalData) {
                this.updateSignalsUI(signalData);
            }

            // Layer 3: Lab Decision Support
            const labData = await this.fetchLab(symbol, tf);
            if (labData) {
                this.updateLabUI(labData);
            }
            // Layer 4: AI Learning Telemetry (Local Audit Log)
            const learnData = await this.fetchLearning();
            if (learnData) {
                this.updateLearningUI(learnData);
            }
        } catch (error) {
            console.error('❌ Dashboard sync failed:', error);
        }
    },

    async fetchLearning() {
        try {
            // Fetch the local JSON export from the audit log
            const response = await fetch(`./learning_data.json?t=${Date.now()}`);
            if (!response.ok) return null;
            return await response.json();
        } catch (e) {
            return null;
        }
    },

    updateLearningUI(data) {
        document.getElementById('learn-samples').innerText = data.total_samples || 0;
        document.getElementById('learn-avg-conf').innerText = `${(data.avg_confidence * 100).toFixed(1)}%`;
        document.getElementById('learn-peak-conf').innerText = `${(data.peak_confidence * 100).toFixed(1)}%`;

        const trendEl = document.getElementById('learn-trend');
        trendEl.innerText = data.current_trend;
        trendEl.style.color = data.current_trend === 'RISING' ? 'var(--highlight)' : (data.current_trend === 'FALLING' ? '#ef4444' : 'var(--text-dim)');

        const updateDate = new Date(data.last_updated);
        document.getElementById('learn-last-update').innerText = updateDate.toLocaleTimeString();

        // Performance Summary Update
        if (data.performance) {
            document.getElementById('perf-total').innerText = data.performance.total_signals || 0;
            document.getElementById('perf-wins').innerText = data.performance.wins || 0;
            document.getElementById('perf-losses').innerText = data.performance.losses || 0;
            document.getElementById('perf-winrate').innerText = `${data.performance.win_rate}%`;

            if (data.performance.details) {
                const d = data.performance.details;
                document.getElementById('breakdown-buy').innerText = `${d.BUY.wins}/${d.BUY.total}`;
                document.getElementById('breakdown-sell').innerText = `${d.SELL.wins}/${d.SELL.total}`;
                document.getElementById('breakdown-hold').innerText = `${d.HOLD.wins}/${d.HOLD.total}`;
            }
        }

        // Mini Chart
        const chart = document.getElementById('learning-chart');
        if (chart && data.recent_history) {
            chart.innerHTML = data.recent_history.map(h => `
                <div style="flex: 1; background: var(--accent); height: ${h.v}%; opacity: ${h.v / 100 + 0.2}; border-radius: 2px;" title="${h.v}% at ${new Date(h.t).toLocaleTimeString()}"></div>
            `).join('');
        }
    },

    async fetchSignals() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        try {
            const baseUrl = 'https://signalgeniusai-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/active?t=${Date.now()}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) return null;
            return await response.json();
        } catch (e) {
            clearTimeout(timeoutId);
            return null;
        }
    },

    updateSignalsUI(signals) {
        const container = document.getElementById('signals-list-container');
        if (!container) return;

        if (!signals || signals.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-dim); border: 1px dashed var(--border); border-radius: 12px;">
                    Awaiting next high-confidence moment...
                </div>
            `;
            return;
        }

        container.innerHTML = signals.map(sig => `
            <div style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 4px;">ASSET / TF</div>
                    <div style="font-weight: 800; color: var(--text-main);">${sig.asset} / ${sig.timeframe}</div>
                </div>
                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 4px;">DIRECTION</div>
                    <div style="font-weight: 800; color: ${sig.direction === 'BUY' ? 'var(--highlight)' : '#ef4444'};">${sig.direction}</div>
                </div>
                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 4px;">CONFIDENCE</div>
                    <div style="font-weight: 800; color: var(--text-main);">${Math.round(sig.ai_confidence * 100)}%</div>
                </div>
                <div style="grid-column: 1 / -1; height: 1px; background: var(--border); margin: 8px 0;"></div>
                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 4px;">ENTRY RANGE</div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.9rem;">${parseFloat(sig.entry_low).toFixed(5)} - ${parseFloat(sig.entry_high || sig.entry_low).toFixed(5)}</div>
                </div>
                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 4px;">TAKE PROFIT</div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.9rem; color: var(--highlight);">${parseFloat(sig.tp).toFixed(5)}</div>
                </div>
                <div>
                    <div class="label-tiny" style="color: var(--text-dim).7px; margin-bottom: 4px;">STOP LOSS</div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.9rem; color: #ef4444;">${parseFloat(sig.sl).toFixed(5)}</div>
                </div>
                <div style="grid-column: 1 / -1; display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--text-dim); margin-top: 8px;">
                    <span>MODE: ${sig.strategy || 'Quantix Engine'}</span>
                    <span>GENERATED: ${new Date(sig.generated_at).toLocaleTimeString()}</span>
                </div>
            </div>
        `).join('');
    },

    async fetchCore(symbol, tf) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/internal/feature-state/structure?symbol=${symbol}&tf=${tf}&period=1mo`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            const data = await response.json();
            return response.ok ? data : null;
        } catch (e) {
            clearTimeout(timeoutId);
            return null;
        }
    },

    async fetchLab(symbol, tf) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/lab/signal-candidate?symbol=${symbol}&tf=${tf}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (response.status === 403 || !response.ok) return null;
            return await response.json();
        } catch (e) {
            clearTimeout(timeoutId);
            return null;
        }
    },

    updateCoreUI(data) {
        const elements = {
            state: document.getElementById('core-state'),
            confidence: document.getElementById('core-confidence'),
            evidence: document.getElementById('evidence-container')
        };

        if (elements.state) {
            const state = (data.state || 'UNKNOWN').toUpperCase();
            elements.state.innerText = state;
            elements.state.style.color = state.includes('BULLISH') ? 'var(--highlight)' : (state.includes('BEARISH') ? 'var(--warning)' : 'var(--text-dim)');
        }

        if (elements.confidence) {
            elements.confidence.innerText = `${((data.confidence || 0) * 100).toFixed(1)}%`;
        }

        // Populate evidence if data exists
        if (elements.evidence && data.evidence && Array.isArray(data.evidence)) {
            elements.evidence.innerHTML = data.evidence.map(item => `
                <div style="padding: 16px; background: rgba(0,0,0,0.2); border-radius: 10px; border: 1px solid var(--border);">
                    <div style="font-size: 0.65rem; color: var(--accent); margin-bottom: 8px;">ENGINE_TRACE</div>
                    <div style="font-size: 0.85rem; color: var(--text-main);">${item}</div>
                </div>
            `).join('');
        }
    },

    updateTelemetry(latency) {
        const hb = document.getElementById('heartbeat-value');
        if (hb) {
            hb.innerText = `${latency}ms`;
        }
        console.log(`📡 Latency: ${latency}ms`);
    },

    updateLabUI(data) {
        // Lab UI is minimal in new dashboard, handled by core capabilities card mostly
    }
};

document.addEventListener('DOMContentLoaded', () => DASHBOARD.init());
