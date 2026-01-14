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
        // Try multiple ID variants to support different page structures
        const elements = {
            total: document.getElementById('total-candles-sidebar') || document.getElementById('total-ingested-sidebar'),
            learning: document.getElementById('learning-candles-sidebar') || document.getElementById('learning-status-sidebar'),
            weight: document.getElementById('avg-weight-sidebar') || document.getElementById('alpha-weight-sidebar')
        };

        if (elements.total) elements.total.innerText = (data.total_ingested || 0).toLocaleString();
        if (elements.learning) elements.learning.innerText = (data.total_learning || 0).toLocaleString();
        if (elements.weight) elements.weight.innerText = (data.avg_weight || 0).toFixed(2);

        // Subtle highlight animation on change
        if (elements.learning && data.total_learning > 0) {
            elements.learning.style.color = '#00f2ff';
            elements.learning.style.textShadow = '0 0 10px rgba(0, 242, 255, 0.5)';
            setTimeout(() => {
                elements.learning.style.color = '';
                elements.learning.style.textShadow = '';
            }, 2000);
        }
    }

};

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', () => UI_MANAGER.init());
