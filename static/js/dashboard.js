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
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/signals/telemetry?t=${Date.now()}`, {
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

    updateLearningUI(data) {
        const setTxt = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.innerText = val;
        };

        setTxt('learn-samples', data.total_samples || 0);
        setTxt('learn-avg-conf', `${(data.avg_confidence * 100).toFixed(1)}%`);
        setTxt('learn-peak-conf', `${(data.peak_confidence * 100).toFixed(1)}%`);

        const trendEl = document.getElementById('learn-trend');
        if (trendEl) {
            trendEl.innerText = data.current_trend;
            trendEl.style.color = data.current_trend === 'RISING' ? 'var(--highlight)' : (data.current_trend === 'FALLING' ? '#ef4444' : 'var(--text-dim)');
        }

        if (data.last_updated) {
            const updateDate = new Date(data.last_updated);
            setTxt('learn-last-update', updateDate.toLocaleTimeString());
        }

        // Performance Summary Update
        if (data.performance) {
            const total = data.performance.total_signals || 0;
            const wins = data.performance.wins || 0;
            const losses = data.performance.losses !== undefined ? data.performance.losses : (total - wins);

            setTxt('perf-total', total);
            setTxt('perf-wins', wins);
            setTxt('perf-losses', losses);
            setTxt('perf-winrate', `${data.performance.win_rate}%`);

            if (data.performance.details) {
                const d = data.performance.details;
                setTxt('breakdown-buy', `${d.BUY.wins}/${d.BUY.total}`);
                setTxt('breakdown-sell', `${d.SELL.wins}/${d.SELL.total}`);
                setTxt('breakdown-hold', `${d.HOLD.wins}/${d.HOLD.total}`);
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
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/signals/active?t=${Date.now()}`, {
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

        container.innerHTML = signals.map(sig => {
            const entry = parseFloat(sig.entry_low);
            const tp = parseFloat(sig.tp);
            const sl = parseFloat(sig.sl);

            // Calculate Pip Distance (for EURUSD 1 pip = 0.0001)
            const tpPips = Math.round(Math.abs(tp - entry) * 10000 * 10) / 10;
            const slPips = Math.round(Math.abs(entry - sl) * 10000 * 10) / 10;
            const rr = sig.reward_risk_ratio || (tpPips / slPips).toFixed(2);

            return `
            <div style="background: rgba(13, 17, 23, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 24px; display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 20px; position: relative; overflow: hidden;">
                <!-- Side highlight based on direction -->
                <div style="position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: ${sig.direction === 'BUY' ? 'var(--highlight)' : '#ef4444'};"></div>
                
                <div style="grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                     <div>
                        <span style="font-weight: 800; color: var(--text-main); font-size: 1.2rem;">${sig.asset}</span>
                        <span style="color: var(--text-dim); font-size: 0.8rem; margin-left: 8px;">${sig.timeframe}</span>
                     </div>
                     <div style="background: ${sig.direction === 'BUY' ? 'rgba(56, 189, 248, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${sig.direction === 'BUY' ? 'var(--highlight)' : '#ef4444'}; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; border: 1px solid ${sig.direction === 'BUY' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(239, 68, 68, 0.2)'};">
                        ${sig.direction}
                     </div>
                </div>

                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 6px; letter-spacing: 0.05em;">ENTRY PRICE</div>
                    <div style="font-family: 'JetBrains Mono'; font-weight: 700; color: var(--text-main); font-size: 1.1rem;">
                        ${entry.toFixed(5)}
                    </div>
                    <div style="font-size: 0.65rem; color: var(--text-dim); margin-top: 4px;">Confidence: ${Math.round(sig.ai_confidence * 100)}%</div>
                </div>

                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 6px; letter-spacing: 0.05em;">PROFIT TARGET</div>
                    <div style="font-family: 'JetBrains Mono'; font-weight: 700; color: var(--highlight); font-size: 1.1rem;">
                        ${tp.toFixed(5)}
                    </div>
                    <div style="font-size: 0.65rem; color: var(--highlight); margin-top: 4px; opacity: 0.8;">+${tpPips} pips</div>
                </div>

                <div>
                    <div class="label-tiny" style="color: var(--text-dim); margin-bottom: 6px; letter-spacing: 0.05em;">STOP LOSS</div>
                    <div style="font-family: 'JetBrains Mono'; font-weight: 700; color: #ef4444; font-size: 1.1rem;">
                        ${sl.toFixed(5)}
                    </div>
                    <div style="font-size: 0.65rem; color: #ef4444; margin-top: 4px; opacity: 0.8;">-${slPips} pips</div>
                </div>

                <div style="grid-column: 1 / -1; height: 1px; background: var(--border); margin: 0;"></div>

                <div style="grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem;">
                    <div style="display: flex; gap: 16px; color: var(--text-dim);">
                        <span>RR: <strong style="color: var(--text-main);">${rr}</strong></span>
                        <span>Strategy: <strong style="color: var(--text-main);">${sig.strategy || 'Alpha v1'}</strong></span>
                    </div>
                    <div style="color: var(--text-dim);">
                        Generated: ${new Date(sig.generated_at).toLocaleTimeString()}
                    </div>
                </div>
            </div>
            `;
        }).join('');
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
