const API_CONFIG = {
    // FORCE PRODUCTION ENVIRONMENT
    getBaseUrl: () => {
        const productionUrl = 'https://quantixaicore-production.up.railway.app';
        // Add cache buster to the URL for every fetch to prevent stale 502s
        const buster = `?t=${Date.now()}`;
        return `${productionUrl}/api/v1`;
    },
    // For direct string usage
    BASE_URL: 'https://quantixaicore-production.up.railway.app/api/v1',
    // Helper for cache busting query params
    getBuster: () => `_=${Date.now()}`
};

// Make it globally accessible across all scripts
window.API_CONFIG = API_CONFIG;
