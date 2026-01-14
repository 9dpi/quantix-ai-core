import API_CONFIG from './api.js';

const API_BASE = API_CONFIG.getBaseUrl();

document.addEventListener('DOMContentLoaded', () => {
    initIngestion();
});

function initIngestion() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const fileNameDisplay = document.getElementById('file-name');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                fileNameDisplay.innerText = `READY: ${fileInput.files[0].name}`;
            }
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener('click', async (e) => {
            handleUpload();
        });
    }

    fetchAuditLogs();
}

async function handleUpload() {
    const btn = document.getElementById('upload-btn');
    const asset = document.getElementById('asset-symbol').value;
    const timeframe = document.getElementById('timeframe').value;
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) {
        showError("SELECT_SOURCE_CSV_REQUIRED");
        return;
    }

    btn.innerText = "EXECUTING PIPELINE...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('asset', asset);
    formData.append('timeframe', timeframe);
    formData.append('source', 'operator_dashboard');

    try {
        const response = await fetch(`${API_BASE}/ingestion/csv`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            // Success - refresh the UI
            if (typeof UI_MANAGER !== 'undefined') {
                UI_MANAGER.refreshGlobalStats();
            }
            fetchAuditLogs();
            btn.innerText = "INGESTION_COMPLETE";
            setTimeout(() => {
                btn.innerText = "EXECUTE INGESTION SEQUENCE";
                btn.disabled = false;
            }, 3000);
        } else {
            const errorMsg = result.detail || result.message || "PIPELINE_ERROR";
            showError(`[${response.status}] ${errorMsg}`);
            btn.disabled = false;
            btn.innerText = "EXECUTE INGESTION SEQUENCE";
        }
    } catch (e) {
        showError(`NETWORK_FAILURE: ${e.message}`);
        btn.disabled = false;
        btn.innerText = "EXECUTE INGESTION SEQUENCE";
    }
}

function showError(msg) {
    const errorBox = document.getElementById('error-box');
    const errorMsg = document.getElementById('error-msg');
    if (errorBox && errorMsg) {
        errorBox.style.display = 'block';
        errorMsg.innerText = msg;
        setTimeout(() => {
            errorBox.style.display = 'none';
        }, 5000);
    }
}

async function fetchAuditLogs() {
    const container = document.getElementById('audit-log');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/ingestion/audit-log?limit=8`);
        const data = await response.json();

        if (data.status === 'success' && data.logs.length > 0) {
            container.innerHTML = data.logs.map(log => `
                <div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 4px; margin-bottom: 8px; font-size: 0.7rem; border: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: var(--accent); font-weight: 700;">${log.asset} / ${log.timeframe.toUpperCase()}</span>
                        <span style="color: var(--text-dim); font-size: 0.6rem;">${new Date(log.ingested_at).toLocaleTimeString()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; opacity: 0.8;">
                        <span>Rows: ${log.total_rows.toLocaleString()}</span>
                        <span style="color: var(--highlight);">Alpha Wt: ${log.avg_learning_weight.toFixed(2)}</span>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: var(--text-dim); font-size: 0.7rem; text-align: center; padding: 20px; border: 1px dashed var(--border);">No recent activities.</p>';
        }
    } catch (e) {
        console.error('Audit Log Sync Failed');
    }
}
