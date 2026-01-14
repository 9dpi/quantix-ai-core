/**
 * Quantix AI Core - Global API Configuration
 */

const API_CONFIG = {
    // Determine the API Base URL based on where the app is running
    // If on localhost, use local backend. If on GitHub Pages, use Railway backend.
    getBaseUrl: () => {
        const hostname = window.location.hostname;
        const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

        // --- PRODUCTION URL ---
        // IMPORTANT: Replace this with your actual Railway APP URL once deployed
        // Example: https://quantix-ai-backend.up.railway.app
        const productionUrl = 'https://quantix-ai-core-production.up.railway.app';

        const localUrl = 'http://localhost:8000';

        const base = isLocal ? localUrl : productionUrl;

        // Ensure version prefix matches backend settings.API_PREFIX
        return `${base}/api/v1`;
    }
};

export default API_CONFIG;
