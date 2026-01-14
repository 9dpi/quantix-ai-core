// Quantix AI Core - Global API Configuration (PRODUCTION)
const API_CONFIG = {
    // FORCE PRODUCTION ENVIRONMENT
    getBaseUrl: () => {
        // --- PRODUCTION URL ---
        const productionUrl = 'https://quantixaicore-production.up.railway.app';
        return `${productionUrl}/api/v1`;
    },
    // Adding BASE_URL directly for compatibility with ui_shared.js
    BASE_URL: 'https://quantixaicore-production.up.railway.app/api/v1'
};

// Make it globally accessible across all scripts
window.API_CONFIG = API_CONFIG;
