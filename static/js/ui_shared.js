/**
 * Quantix AI Core - Global UI Manager
 * Handles shared components like Global Learning Engine stats
 */

const UI_MANAGER = {
    async init() {
        console.log('🌐 Quantix UI Manager Initialized');
        await this.refreshGlobalStats();
        this.initMobileMenu();

        // Refresh stats every 30 seconds
        setInterval(() => this.refreshGlobalStats(), 30000);
    },

    initMobileMenu() {
        const toggle = document.getElementById('menu-toggle');
        const nav = document.getElementById('main-nav');

        if (toggle && nav) {
            toggle.addEventListener('click', () => {
                nav.classList.toggle('active');
                toggle.innerText = nav.classList.contains('active') ? '✕' : '☰';
            });
        }
    },

    async refreshGlobalStats() {
        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';

            const buster = typeof API_CONFIG !== 'undefined' ? API_CONFIG.getBuster() : `t=${Date.now()}`;
            const response = await fetch(`${baseUrl}/ingestion/global-stats?${buster}`);
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                this.updateSidebarUI(result.data);
                // Dispatch event for other scripts to know data has arrived
                document.dispatchEvent(new CustomEvent('data-refreshed', { detail: result.data }));
            }
        } catch (error) {
            console.error('❌ Failed to fetch global stats:', error);
        }
    },

    updateSidebarUI(data) {
        // Correct IDs for the new layout
        const elements = {
            total: document.getElementById('total-ingested-sidebar') || document.getElementById('total-candles-sidebar'),
            learning: document.getElementById('learning-status-sidebar') || document.getElementById('learning-candles-sidebar'),
            weight: document.getElementById('alpha-weight-sidebar') || document.getElementById('avg-weight-sidebar'),
            time: document.getElementById('last-update-time')
        };

        if (elements.total) elements.total.innerText = (data.total_ingested || 0).toLocaleString();
        if (elements.learning) {
            elements.learning.innerText = (data.total_learning || 0).toLocaleString();
        }
        if (elements.weight) elements.weight.innerText = (data.avg_weight || 0).toFixed(2);

        if (elements.time) {
            const now = new Date();
            elements.time.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
    }


};

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', () => UI_MANAGER.init());
