/**
 * Quantix AI Core - Global API Configuration
 */

const API_CONFIG = {
    // Determine the API Base URL based on where the app is running
    // If on localhost, use local backend. If on GitHub Pages, use Railway backend.
    getBaseUrl: () => {
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

        // Replace this with your actual Railway backend URL
        const productionUrl = 'https://quantix-ai-core-production.up.railway.app';
        const localUrl = 'http://localhost:8000';

        return `${isLocal ? localUrl : productionUrl}/api/v1`;
    }
};

export default API_CONFIG;
