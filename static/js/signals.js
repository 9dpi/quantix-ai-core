/**
 * Quantix AI Core - Signal Engine Lab (Experimental)
 * Snapshot-based logic for Market References.
 * 
 * v2.0 - Robust / Defensive / Async-Safe
 */

const SIGNALS = {
    isLoading: false,

    async init() {
        console.log('🧪 Signal Engine Lab Initializing...');

        // ✅ FIX 1: Always fetch on load
        await this.loadReferences();

        // ✅ FIX 2: Refetch on visibility change (Tab Switch / Return)
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === "visible") {
                console.log('👀 Tab visible - refreshing signals...');
                this.loadReferences();
            }
        });
    },

    async loadReferences() {
        // Simple debounce to prevent double-click spam, but allows refetch
        if (this.isLoading) return;
        this.isLoading = true;

        const container = document.getElementById('signals-container');
        const syncLabel = document.getElementById('last-sync-time');
        const symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"];

        // Set Loading State (Reset View)
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 100px; color: var(--text-dim);">
                <div class="pulse-small" style="margin: 0 auto 20px;"></div>
                <div style="font-size: 0.9rem;">Synchronizing Intelligence Snapshots...</div>
                <div style="font-size: 0.75rem; margin-top: 8px; color: var(--text-dim); opacity: 0.6;">Connecting to Signal Engine</div>
            </div>
        `;

        try {
            // ... rest of logic stays same, will be handled by existing code flow
            const results = [];
            // Start fetching
            const promises = symbols.map(symbol => this.fetchLabSnapshot(symbol, "H4"));
            const fetchedData = await Promise.all(promises);

            // Filter out nulls
            fetchedData.forEach(data => {
                if (data) results.push(data);
            });

            container.innerHTML = '';

            if (results.length > 0) {
                // ✅ SUCCESS: Cache the fresh data
                localStorage.setItem('qt_signals_cache', JSON.stringify({
                    timestamp: Date.now(),
                    data: results
                }));

                results.forEach(data => this.renderLabCard(container, data));

                if (syncLabel) syncLabel.innerText = `Last snapshot: ${new Date().toLocaleTimeString()} UTC`;
            } else {
                // ❌ FAILURE: Try to load from cache
                console.warn("⚠️ Fetch failed, attempting to load from cache...");
                this.loadFromCache(container);
            }

        } catch (e) {
            console.error("🔥 Critical Error in Signals Load:", e);
            // ❌ DRASTIC FAILURE: Try cache as last resort
            this.loadFromCache(container);
        } finally {
            this.isLoading = false;
        }
    },

    loadFromCache(container) {
        try {
            const cached = localStorage.getItem('qt_signals_cache');
            if (cached) {
                const parsed = JSON.parse(cached);
                const timeDiff = Math.round((Date.now() - parsed.timestamp) / 60000); // Minutes

                container.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; padding: 16px; margin-bottom: 24px; background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; color: var(--text-main); font-size: 0.85rem; line-height: 1.5;">
                        <strong style="color: var(--accent); display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em;">ℹ️ Snapshot Reference Mode</strong>
                        Market references are generated from Quantix Lab deterministic logic.<br>
                        <span style="color: var(--text-dim); font-size: 0.75rem;">For evaluation & research only. Not real-time trading signals.</span>
                    </div>
                `;

                parsed.data.forEach(data => this.renderLabCard(container, data));
            } else {
                this.renderEmptyState(container);
            }
        } catch (cacheErr) {
            console.error("Cache load failed", cacheErr);
            this.renderEmptyState(container);
        }
    },

    async fetchLabSnapshot(symbol, tf) {
        // Strict Timeout Guard
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';
            // Use correct API params (backend expects uppercase)
            // Added cache buster to prevent stale 304 responses
            const response = await fetch(`${baseUrl}/lab/market-reference?symbol=${symbol}&tf=${tf}&_=${Date.now()}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                console.warn(`⚠️ API Error ${response.status} for ${symbol}`);
                return null;
            }

            const data = await response.json();

            // Defensive Data Validation
            if (!data || !data.trade_bias) {
                console.error(`❌ Invalid data format for ${symbol}`, data);
                return null;
            }

            return data;

        } catch (e) {
            clearTimeout(timeoutId);
            if (e.name === 'AbortError') {
                console.error(`🕒 Timeout fetching ${symbol}`);
            } else {
                console.error(`❌ Network error for ${symbol}:`, e);
            }
            return null;
        }
    },

    renderLabCard(container, data) {
        // Defensive default values
        const bias = data.trade_bias || "UNKNOWN";
        const strength = data.bias_strength || "N/A";
        const confidence = data.confidence || 0;
        const colorKey = data.ui_color || "gray";

        const card = document.createElement('div');
        card.className = 'reference-card';

        // UI Color Mapping
        const colors = {
            "gray": "var(--text-dim)",
            "yellow": "#facc15",
            "green": "var(--highlight)",
            "blue": "#3b82f6",
            "fire": "#ef4444"
            // Note: fire is usually red/orange for high conviction sell or buy. 
            // Currently backend logic maps high conviction to 'fire'.
        };

        // Determine specific decent accent color
        let accentColor = colors[colorKey] || "var(--text-dim)";

        // Icon mapping
        let icon = "⚪";
        if (bias.includes("BUY")) icon = "🟢";
        if (bias.includes("SELL")) icon = "🔴";
        if (colorKey === 'fire') icon = "🔥";
        if (bias === 'WAIT') icon = "✋";
        if (bias === 'NO TRADE') icon = "⛔";

        // Price Levels Safety Check
        const levels = data.price_levels || { entry_zone: [0, 0], take_profit: 0, stop_loss: 0 };
        const entryText = levels.entry_zone ? `${levels.entry_zone[0]} — ${levels.entry_zone[1]}` : "—";
        const tradeDetails = data.trade_details || { target_pips: 0, risk_reward: 0, trade_type: "N/A" };

        const expiresAt = data.expiry?.expires_at ? new Date(data.expiry.expires_at) : null;
        const timeString = expiresAt ? expiresAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown';
        const ttlMinutes = data.expiry?.ttl_seconds ? Math.ceil(data.expiry.ttl_seconds / 60) : 0;
        const genTime = data.meta?.generated_at ? new Date(data.meta.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now';

        let footerStatus = `⏳ Next Snapshot: ${timeString} (${ttlMinutes}m)`;
        if (ttlMinutes <= 0) footerStatus = `🔄 Update Available`;

        card.innerHTML = `
            <div style="position: absolute; top: 12px; left: 12px; display: flex; gap: 6px;">
                 <span style="font-size: 0.5rem; background: rgba(255,255,255,0.05); color: var(--text-dim); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--border);">SNAPSHOT</span>
            </div>

            <div class="card-badge" style="background: rgba(0,0,0,0.3); border: 1px solid ${accentColor}; color: ${accentColor}; top: 24px;">
                ${bias}
            </div>
            
            <div class="symbol-title" style="margin-top: 10px;">${data.asset}</div>
            <span class="timeframe-label">⏳ ${data.timeframe} • ${data.session || 'Global'}</span>
            
            <div style="margin: 20px 0;">
                <div style="font-size: 0.9rem; font-weight: 800; color: ${accentColor}; margin-bottom: 4px;">
                    ${icon} ${strength} Signal
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="confidence-meter" style="height: 4px; background: rgba(255,255,255,0.1);">
                        <div class="confidence-fill" style="width: ${Math.min(confidence * 100, 100)}%; height: 100%; background: ${accentColor}; border-radius: 100px;"></div>
                    </div>
                    <span style="font-size: 0.7rem; font-weight: 700;">${(confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="level-grid" style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div class="level-item" style="grid-column: 1 / -1; background: transparent; border: none; padding: 0; margin-bottom: 12px;">
                    <div class="level-label">💰 Entry Zone</div>
                    <div class="level-value" style="font-size: 1.1rem; color: var(--text-main);">${entryText}</div>
                </div>
                <div class="level-item" style="background: transparent; border: none; padding: 0;">
                    <div class="level-label">🎯 Target</div>
                    <div class="level-value" style="color: var(--highlight);">${levels.take_profit || '—'}</div>
                </div>
                <div class="level-item" style="background: transparent; border: none; padding: 0; text-align: right;">
                    <div class="level-label">🛑 Stop</div>
                    <div class="level-value" style="color: #ef4444;">${levels.stop_loss || '—'}</div>
                </div>
            </div>

            <div style="margin: 20px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.75rem;">
                <div style="color: var(--text-dim);">Potential: <span style="color: var(--text-main); font-weight: 700;">${tradeDetails.target_pips > 0 ? '+' + tradeDetails.target_pips : '—'} pips</span></div>
                <div style="color: var(--text-dim); text-align: right;">RRR: <span style="color: var(--text-main); font-weight: 700;">${tradeDetails.risk_reward > 0 ? '1:' + tradeDetails.risk_reward : '—'}</span></div>
            </div>
            
            <div class="meta-footer" style="margin-top: 10px; font-size: 0.6rem; display: flex; justify-content: space-between;">
                <div style="opacity: 0.7;">Gen: ${genTime} UTC</div>
                <div style="font-weight: 700; color: var(--accent);">${footerStatus}</div>
            </div>
        `;

        container.appendChild(card);
    },

    renderErrorCard(container, assetName) {
        const div = document.createElement('div');
        div.className = 'reference-card';
        div.style.borderColor = 'var(--warning)';
        div.innerHTML = `
            <div style="color: var(--warning); font-weight: bold;">⚠️ ${assetName} Data Error</div>
            <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 8px;">Could not render signal data. Source returned invalid format.</div>
        `;
        container.appendChild(div);
    },

    renderEmptyState(container) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-dim);">
                <h3>💤 No Signals Generated</h3>
                <p>The signal engine is online but returned no data. Try again shortly.</p>
                <button onclick="SIGNALS.loadReferences()" class="btn-primary" style="margin-top: 16px;">Refresh</button>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => SIGNALS.init());
