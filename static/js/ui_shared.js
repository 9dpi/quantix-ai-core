/**
 * Quantix AI Core - Global UI Manager
 * Handles shared components like Global Learning Engine stats
 */

const UI_MANAGER = {
    async init() {
        console.log('🌐 Quantix UI Manager Initialized');
        await this.refreshGlobalStats();

        // Refresh stats every 30 seconds
        setInterval(() => this.refreshGlobalStats(), 30000);
    },

    async refreshGlobalStats() {
        try {
            // Using API_CONFIG from api.js if available, otherwise fallback
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';

            const response = await fetch(`${baseUrl}/ingestion/global-stats`);
            const result = await response.json();

            if (result.status === 'success') {
                this.updateSidebarUI(result.data);
            }
        } catch (error) {
            console.error('❌ Failed to fetch global stats:', error);
        }
    },

    updateSidebarUI(data) {
        // IDs optimized for 3-column layout
        const elements = {
            total: document.getElementById('total-ingested-sidebar') || document.getElementById('total-candles-sidebar'),
            learning: document.getElementById('learning-status-sidebar') || document.getElementById('learning-candles-sidebar'),
            weight: document.getElementById('alpha-weight-sidebar') || document.getElementById('avg-weight-sidebar'),
            time: document.getElementById('last-update-time')
        };

        if (elements.total) elements.total.innerText = (data.total_ingested || 0).toLocaleString();
        if (elements.learning) {
            elements.learning.innerText = (data.total_learning || 0).toLocaleString();
            elements.learning.style.color = '#38bdf8'; // Sync with Sky Blue
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
