import API_CONFIG from './api.js';

const API_BASE = API_CONFIG.getBaseUrl();

document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

async function initDashboard() {
    console.log("🚀 Initializing Quantix Dashboard...");
    console.log("📍 API Base:", API_BASE);

    // Check API Health
    checkHealth();

    // Fetch Stats
    fetchIngestionStats();

    // Fetch Signals
    fetchSignals();

    // Refresh periodically
    setInterval(fetchSignals, 30000);
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const dot = document.getElementById('api-status');
        if (response.ok) {
            dot.style.background = '#00ff00';
            dot.title = 'API Online';
        } else {
            dot.style.background = '#ff9900';
            dot.title = 'API Error';
        }
    } catch (e) {
        document.getElementById('api-status').style.background = '#ff0000';
    }
}

async function fetchIngestionStats() {
    try {
        const response = await fetch(`${API_BASE}/ingestion/stats`);
        const data = await response.json();

        if (data.status === 'success') {
            const validatedTier = data.tiers.find(t => t.tier === 'validated');
            if (validatedTier) {
                document.getElementById('total-candles').innerText = validatedTier.total_candles.toLocaleString();
            }
        }
    } catch (e) {
        console.error("Failed to fetch stats:", e);
    }
}

async function fetchSignals() {
    const container = document.getElementById('signals-container');

    try {
        const response = await fetch(`${API_BASE}/fx/signals`);
        // Note: For MVP we might use a mock or a simplified endpoint
        // Assuming there's a signals endpoint

        if (!response.ok) throw new Error("API not responding");

        const signals = await response.json();

        if (signals.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No active internal signals found.</p></div>';
            return;
        }

        container.innerHTML = signals.map(sig => `
            <div class="signal-card">
                <div>
                    <strong style="color: var(--accent); font-size: 1.2rem;">${sig.asset} ${sig.direction}</strong>
                    <div style="font-size: 0.85rem; color: #666;">${sig.timeframe} • Generated ${new Date(sig.generated_at).toLocaleTimeString()}</div>
                </div>
                <div style="text-align: right">
                    <div style="font-weight: 700; color: #00ff00;">${(sig.ai_confidence * 100).toFixed(1)}%</div>
                    <div style="font-size: 0.7rem; color: #555;">PROBABILITY</div>
                </div>
            </div>
        `).join('');

        document.getElementById('active-signals').innerText = signals.length;

    } catch (e) {
        container.innerHTML = '<div class="empty-state"><p>Internal signal engine not broadcasting.</p></div>';
    }
}
