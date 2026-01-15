/**
 * Quantix AI Core - Public Dashboard Manager
 * Implements 3-layer architecture: Core Analysis, Lab Support, and Status.
 */

const DASHBOARD = {
    async init() {
        console.log('🏛️ Quantix Public Dashboard Initializing...');
        await this.refreshContent();

        // Refresh every 5 minutes in production mode
        // setInterval(() => this.refreshContent(), 300000);
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

            // Layer 2: Lab Decision Support
            const labData = await this.fetchLab(symbol, tf);
            if (labData) {
                this.updateLabUI(labData);
            }
        } catch (error) {
            console.error('❌ Dashboard sync failed:', error);
        }
    },

    async fetchCore(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            // Using the production-grade structure endpoint
            const response = await fetch(`${baseUrl}/internal/feature-state/structure?symbol=${symbol}&tf=${tf}&period=1mo`);
            const data = await response.json();
            return response.ok ? data : null;
        } catch (e) { return null; }
    },

    async fetchLab(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/lab/signal-candidate?symbol=${symbol}&tf=${tf}`);
            if (response.status === 403 || !response.ok) return null;
            return await response.json();
        } catch (e) { return null; }
    },

    updateCoreUI(data) {
        const elements = {
            state: document.getElementById('core-state'),
            confidence: document.getElementById('core-confidence'),
            dominance: document.getElementById('core-dominance'),
            trace: document.getElementById('trace-id-sidebar')
        };

        if (elements.state) {
            elements.state.innerText = (data.state || 'UNKNOWN').toUpperCase();
            elements.state.style.color = data.state === 'bullish' ? 'var(--highlight)' : (data.state === 'bearish' ? 'var(--error)' : 'var(--text-dim)');
        }
        if (elements.confidence) {
            elements.confidence.innerText = `${((data.confidence || 0) * 100).toFixed(1)}%`;
        }
        if (elements.dominance) {
            // Check for dominance_ratio or statistics sub-object
            const ratio = data.dominance_ratio || (data.dominance ? data.dominance.bullish / (data.dominance.bearish || 1) : 0);
            elements.dominance.innerText = ratio.toFixed(2);
        }
        if (elements.trace) {
            elements.trace.innerText = data.trace_id || 'manual';
        }
    },

    updateTelemetry(latency) {
        // Update heartbeat text in the infra card
        const latencyEls = document.querySelectorAll('.status-indicator-compact');
        // Simple mock for variety, but latency is real
        console.log(`📡 Latency: ${latency}ms`);
    },

    updateLabUI(data) {
        // Lab UI is minimal in new dashboard, handled by core capabilities card mostly
    }
};

document.addEventListener('DOMContentLoaded', () => DASHBOARD.init());
