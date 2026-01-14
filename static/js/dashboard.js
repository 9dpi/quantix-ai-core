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
            // Layer 1: Core Research
            const coreData = await this.fetchCore(symbol, tf);
            if (coreData) this.updateCoreUI(coreData);

            // Layer 2: Lab Decision Support
            const labData = await this.fetchLab(symbol, tf);
            if (labData) {
                this.updateLabUI(labData);
            } else {
                document.getElementById('lab-section').style.display = 'none';
            }
        } catch (error) {
            console.error('❌ Dashboard sync failed:', error);
        }
    },

    async fetchCore(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/internal/feature-state/structure?symbol=${symbol}&tf=${tf}`);
            return await response.json();
        } catch (e) { return null; }
    },

    async fetchLab(symbol, tf) {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            const response = await fetch(`${baseUrl}/lab/signal-candidate?symbol=${symbol}&tf=${tf}`);
            if (response.status === 403) return null; // Kill switch active
            return await response.json();
        } catch (e) { return null; }
    },

    updateCoreUI(data) {
        const elements = {
            state: document.getElementById('core-state'),
            confidence: document.getElementById('core-confidence'),
            dominance: document.getElementById('core-dominance'),
            evidence: document.getElementById('core-evidence'),
            trace: document.getElementById('core-trace'),
            time: document.getElementById('core-time')
        };

        if (elements.state) {
            elements.state.innerText = (data.state || 'UNKNOWN').toUpperCase();
            elements.state.style.color = data.state === 'bullish' ? 'var(--highlight)' : (data.state === 'bearish' ? 'var(--error)' : 'var(--text-dim)');
        }
        if (elements.confidence) elements.confidence.innerText = `${((data.confidence || 0) * 100).toFixed(1)}%`;
        if (elements.dominance) elements.dominance.innerText = (data.dominance_ratio || 0).toFixed(2);
        if (elements.trace) elements.trace.innerText = data.trace_id || 'manual';
        if (elements.time) elements.time.innerText = new Date().toISOString().replace('T', ' ').substring(0, 16) + ' UTC';

        if (elements.evidence && data.evidence) {
            elements.evidence.innerHTML = data.evidence.map(ev => `<li>${ev}</li>`).join('');
        }
    },

    updateLabUI(data) {
        const labSection = document.getElementById('lab-section');
        const elements = {
            decision: document.getElementById('lab-decision'),
            reason: document.getElementById('lab-reason'),
            validity: document.getElementById('lab-validity'),
            ruleset: document.getElementById('lab-ruleset')
        };

        if (labSection) labSection.style.display = 'block';
        if (elements.decision) {
            elements.decision.innerText = data.decision.replace('_', ' ');
            elements.decision.style.color = data.decision.includes('BUY') ? 'var(--highlight)' : (data.decision.includes('SELL') ? 'var(--error)' : 'var(--text-dim)');
        }
        if (elements.reason) elements.reason.innerText = data.explain[0] || 'No specific reason provided.';
        if (elements.validity) elements.validity.innerText = data.valid_for || 'Unknown';
        if (elements.ruleset) elements.ruleset.innerText = 'signal_mapping_v1';
    }
};

document.addEventListener('DOMContentLoaded', () => DASHBOARD.init());
