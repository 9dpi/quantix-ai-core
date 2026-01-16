const API_CONFIG = {
    // AUTOMATIC LOCAL/PROD DETECTION
    getBaseUrl: () => {
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const productionUrl = 'https://quantixaicore-production.up.railway.app';
        const localUrl = 'http://127.0.0.1:8001';

        const baseUrl = isLocal ? localUrl : productionUrl;
        return `${baseUrl}/api/v1`;
    },
    // For direct string usage
    get BASE_URL() {
        return this.getBaseUrl();
    },
    // Helper for cache busting query params
    getBuster: () => `_=${Date.now()}`
};

// Make it globally accessible across all scripts
window.API_CONFIG = API_CONFIG;
