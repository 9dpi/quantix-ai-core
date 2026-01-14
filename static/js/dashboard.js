/**
 * Quantix AI Core - Dashboard Management
 * Handles Real-time Signals and Intelligence Feed
 */

const DASHBOARD = {
    async init() {
        console.log('🎯 Dashboard Logic Initialized');
        this.renderDemoSignals();

        // Listen for global data updates to refresh UI specific parts
        document.addEventListener('data-refreshed', (e) => {
            console.log('🔄 Dashboard informed of data refresh');
        });
    },

    renderDemoSignals() {
        const container = document.getElementById('signal-container');
        if (!container) return;

        const demoSignals = [
            { pair: 'EURUSD/X', action: 'SNIPER_LONG', confidence: '94.2%', time: '2m ago', zone: '1.08510 - 1.08530' },
            { pair: 'EURUSD/X', action: 'REVERSAL_SCAN', confidence: '82.1%', time: '15m ago', zone: '1.08850' },
            { pair: 'GBPUSD/X', action: 'WATCHING', confidence: '--', time: 'Ongoing', zone: 'Market_Scan' }
        ];

        container.innerHTML = demoSignals.map(sig => `
            <div class="alert-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="alert-pair">${sig.pair}</span>
                    <span style="font-size: 0.6rem; font-weight: 800; color: ${sig.action.includes('LONG') ? '#10b981' : '#f43f5e'}">${sig.action}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                    <span style="font-size: 0.65rem; color: var(--text-dim);">Conf: ${sig.confidence}</span>
                    <span style="font-size: 0.65rem; color: var(--text-main);">${sig.zone}</span>
                </div>
                <div class="alert-time">${sig.time}</div>
            </div>
        `).join('');
    }
};

// Auto-start
document.addEventListener('DOMContentLoaded', () => DASHBOARD.init());
