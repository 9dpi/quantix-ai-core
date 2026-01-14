/**
 * Quantix AI Core - Global API Configuration (PRODUCTION)
 */

const API_CONFIG = {
    // FORCE PRODUCTION ENVIRONMENT
    getBaseUrl: () => {
        // --- PRODUCTION URL ---
        // This is the engine's primary heartbeat on Railway
        const productionUrl = 'https://quantixaicore-production.up.railway.app';

        // Return production URL directly to ensure online connectivity
        return `${productionUrl}/api/v1`;
    }
};

// Make API_CONFIG globally accessible
window.API_CONFIG = API_CONFIG;
