// API_CONFIG is loaded via static/js/api.js script tag as a global
const API_BASE = window.API_CONFIG ? window.API_CONFIG.getBaseUrl() : 'https://quantixaicore-production.up.railway.app/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    initIngestion();
});

function initIngestion() {
    const dropZoneWrapper = document.getElementById('drop-zone-wrapper');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const fileNameDisplay = document.getElementById('file-name');

    // DEBUG LOG
    console.log('📌 Ingestion Init:', { dropZoneWrapper, dropZone, fileInput, uploadBtn });

    if (dropZoneWrapper && fileInput) {
        // Force pointer cursor
        dropZoneWrapper.style.cursor = 'pointer';

        // Use wrapper for click events (more reliable)
        dropZoneWrapper.onclick = (e) => {
            console.log('🖱️ Drop zone clicked');
            e.preventDefault();
            fileInput.click();
        };

        const browseBtn = document.getElementById('browse-btn');
        if (browseBtn) {
            browseBtn.onclick = (e) => {
                console.log('🖱️ Browse button clicked');
                e.preventDefault();
                fileInput.click();
            };
        }

        fileInput.onchange = () => {
            if (fileInput.files.length) {
                console.log('📝 File selected:', fileInput.files[0].name);
                if (fileNameDisplay) {
                    fileNameDisplay.innerText = `READY: ${fileInput.files[0].name}`;
                    fileNameDisplay.style.color = 'var(--accent)';
                }
            }
        };

        // Drag & Drop effects on wrapper
        dropZoneWrapper.ondragover = (e) => {
            e.preventDefault();
            dropZoneWrapper.style.borderColor = 'var(--accent)';
            dropZoneWrapper.style.background = 'rgba(56, 189, 248, 0.05)';
        };

        dropZoneWrapper.ondragleave = () => {
            dropZoneWrapper.style.borderColor = '';
            dropZoneWrapper.style.background = '';
        };

        dropZoneWrapper.ondrop = (e) => {
            e.preventDefault();
            dropZoneWrapper.style.borderColor = '';
            dropZoneWrapper.style.background = '';
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                if (fileNameDisplay) {
                    fileNameDisplay.innerText = `READY: ${fileInput.files[0].name}`;
                }
            }
        };
    }

    if (uploadBtn) {
        uploadBtn.onclick = async () => {
            console.log('🚀 Execute button clicked');
            handleUpload();
        };
    }

    fetchAuditLogs();
}

async function handleUpload() {
    const btn = document.getElementById('upload-btn');
    const assetInput = document.getElementById('asset-symbol');
    const timeframeInput = document.getElementById('timeframe');
    const fileInput = document.getElementById('file-input');

    const asset = assetInput ? assetInput.value : 'EURUSD';
    const timeframe = timeframeInput ? timeframeInput.value : 'm15';
    const file = fileInput ? fileInput.files[0] : null;

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
        console.log('📤 Uploading to:', `${API_BASE}/ingestion/csv`);
        const response = await fetch(`${API_BASE}/ingestion/csv`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            console.log('✅ Upload Success:', result);
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
        console.error('❌ Upload Failed:', e);
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
    } else {
        alert(msg);
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
