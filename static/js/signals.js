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
        if (this.isLoading) return;
        this.isLoading = true;

        const container = document.getElementById('signals-container');
        const archiveBody = document.getElementById('archive-tbody-main');
        const syncLabel = document.getElementById('last-sync-time');

        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 100px; color: var(--text-dim);"><div class="pulse-small" style="margin: 0 auto 20px;"></div><div style="font-size: 0.9rem;">Connecting to Quantix Lab Engine...</div></div>`;

        try {
            const baseUrl = typeof API_CONFIG !== 'undefined' ? API_CONFIG.BASE_URL : 'https://quantixaicore-production.up.railway.app/api/v1';

            // 1. Fetch Audit Trail (High Reliability)
            const auditResponse = await fetch(`${baseUrl}/health/audit?_=${Date.now()}`);
            let auditData = null;
            if (auditResponse.ok) {
                auditData = await auditResponse.json();
                this.renderAuditTable(archiveBody, auditData);
            }

            // 2. Fetch Latest Signals (Reasoning)
            const signalResponse = await fetch(`${baseUrl}/latest-lab?_=${Date.now()}`);
            const signals = signalResponse.ok ? await signalResponse.json() : [];

            container.innerHTML = '';

            if (signals && signals.length > 0) {
                signals.forEach(data => this.renderLabCard(container, data));
            } else if (auditData && auditData.latest_heartbeats && auditData.latest_heartbeats.length > 0) {
                // Fallback: Display Audit Heartbeats as Cards if no specific signal candidates yet
                const entries = [...auditData.latest_heartbeats].reverse();
                entries.slice(0, 3).forEach(hbStr => {
                    try {
                        const hb = JSON.parse(hbStr);
                        if (hb.status === 'ANALYZED') {
                            this.renderLabCard(container, hb, true);
                        }
                    } catch (e) { }
                });
            } else {
                this.renderEmptyState(container);
            }

            if (syncLabel) syncLabel.innerText = `Last update: ${new Date().toLocaleTimeString()} UTC`;

        } catch (e) {
            console.error("🔥 Signals Load Failed:", e);
            this.renderEmptyState(container);
        } finally {
            this.isLoading = false;
        }
    },

    renderAuditTable(tbody, data) {
        if (!tbody || !data || !data.latest_heartbeats) return;
        tbody.innerHTML = '';

        const entries = [...data.latest_heartbeats].reverse();
        entries.forEach(line => {
            try {
                const hb = JSON.parse(line);
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid rgba(255,255,255,0.05)';

                const time = new Date(hb.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                const statusColor = hb.status === 'SYSTEM_STARTUP' ? 'var(--warning)' : 'var(--highlight)';

                row.innerHTML = `
                    <td style="padding: 12px; font-family: 'JetBrains Mono'; color: var(--text-dim);">${time}</td>
                    <td style="padding: 12px; color: var(--text-main); font-weight: 700;">${hb.asset || 'SYSTEM'}</td>
                    <td style="padding: 12px; font-size: 0.8rem;">${hb.price ? 'Price: ' + hb.price.toFixed(5) + ' | Conf: ' + (hb.confidence * 100).toFixed(0) + '%' : hb.message}</td>
                    <td style="padding: 12px;"><span style="color: ${statusColor}; font-weight: 800; font-size: 0.7rem;">${hb.status}</span></td>
                `;
                tbody.appendChild(row);
            } catch (e) { }
        });
    },

    renderLabCard(container, data, isHeartbeat = false) {
        const bias = data.direction || (isHeartbeat ? "WAIT" : "WAIT");
        const confidence = data.ai_confidence || (isHeartbeat ? data.confidence : 0);
        const asset = data.asset || "EURUSD";
        const timeframe = data.timeframe || "M15";

        const card = document.createElement('div');
        card.className = 'reference-card';
        if (isHeartbeat) card.style.opacity = '0.85';

        // Dynamic Styling (Signal Genius Style)
        const isBuy = bias === 'BUY';
        const isSell = bias === 'SELL';
        const accentColor = isBuy ? 'var(--highlight)' : (isSell ? '#ef4444' : 'var(--text-dim)');
        const icon = isBuy ? "🟢" : (isSell ? "🔴" : "✋");

        const entryLow = parseFloat(data.entry_low || data.price || 0).toFixed(5);
        const entryHigh = parseFloat(data.entry_high || (data.price ? data.price + 0.0002 : 0)).toFixed(5);
        const tp = parseFloat(data.tp || 0).toFixed(5);
        const sl = parseFloat(data.sl || 0).toFixed(5);

        const timestamp = data.generated_at || data.timestamp;
        const genTime = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Now';

        card.innerHTML = `
            <div style="position: absolute; top: 12px; left: 12px; display: flex; gap: 6px;">
                 <span style="font-size: 0.5rem; background: rgba(0,0,0,0.3); color: var(--accent); padding: 2px 8px; border-radius: 4px; border: 1px solid var(--accent); letter-spacing: 0.1em; font-weight: 800;">UNVERIFIED CANDIDATE</span>
            </div>

            <div class="card-badge" style="background: rgba(0,0,0,0.5); border: 1px solid ${accentColor}; color: ${accentColor}; top: 24px; font-weight: 900;">
                ${bias}
            </div>
            
            <div class="symbol-title" style="margin-top: 15px; font-size: 1.8rem;">${asset}</div>
            <span class="timeframe-label" style="font-size: 0.7rem;">⏳ ${timeframe} • Live Reasoning Stream</span>
            
            <div style="margin: 25px 0;">
                <div style="font-size: 0.9rem; font-weight: 800; color: ${accentColor}; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                    ${icon} AI Confidence: ${(confidence * 100).toFixed(0)}%
                </div>
                <div class="confidence-meter" style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 100px;">
                    <div class="confidence-fill" style="width: ${Math.min(confidence * 100, 100)}%; height: 100%; background: ${accentColor}; border-radius: 100px; box-shadow: 0 0 15px ${accentColor}44;"></div>
                </div>
            </div>
            
            <div class="level-grid" style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 16px; border: 1px solid var(--border); display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div style="grid-column: 1 / -1; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 12px;">
                    <div class="level-label" style="font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">💰 Entry Range</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; font-size: 1.1rem; color: var(--text-main); font-weight: 800;">${entryLow} — ${entryHigh}</div>
                </div>
                <div>
                    <div class="level-label" style="font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">🎯 Take Profit</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; color: var(--highlight); font-weight: 800;">${tp > 0 ? tp : '—'}</div>
                </div>
                <div style="text-align: right;">
                    <div class="level-label" style="font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">🛑 Stop Loss</div>
                    <div class="level-value" style="font-family: 'JetBrains Mono'; color: #ef4444; font-weight: 800;">${sl > 0 ? sl : '—'}</div>
                </div>
            </div>

            <div class="meta-footer" style="margin-top: 20px; font-size: 0.65rem; display: flex; justify-content: space-between; color: var(--text-dim); border-top: 1px solid var(--border); padding-top: 12px;">
                <div style="font-family: 'JetBrains Mono';">GEN: ${genTime} UTC</div>
                <div style="font-weight: 800; color: var(--accent); letter-spacing: 0.05em;">NON-VERIFIED</div>
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
            <div style="grid-column: 1/-1; text-align: center; padding: 100px; color: var(--text-dim);">
                <div class="pulse-small" style="margin: 0 auto 20px; opacity: 0.5;"></div>
                <h3 style="color: var(--text-main); font-weight: 800; margin-bottom: 8px;">Quantix Engine: Scanning Market...</h3>
                <p style="font-size: 0.85rem; max-width: 400px; margin: 0 auto;">Establishing connection to [T0] Live Data Feed. Recent candidates will appear here as they are analyzed.</p>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => SIGNALS.init());
