import API_CONFIG from './api.js';

const API_BASE = API_CONFIG.getBaseUrl();

document.addEventListener('DOMContentLoaded', () => {
    initIngestion();
});

function initIngestion() {
    const form = document.getElementById('upload-form');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('csv-file');

    // Drag and Drop handlers
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            dropZone.querySelector('p').innerText = fileInput.files[0].name;
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        handleUpload();
    });

    fetchAuditLogs();
}

async function handleUpload() {
    const btn = document.getElementById('upload-btn');
    const asset = document.getElementById('asset').value;
    const timeframe = document.getElementById('timeframe').value;
    const file = document.getElementById('csv-file').files[0];

    if (!file) {
        alert("Please select a CSV file");
        return;
    }

    btn.innerText = "Processing Pipeline...";
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
            showSuccess(result);
        } else {
            const errorMsg = result.detail || result.message || "Ingestion failed";
            showError(`[${response.status}] ${errorMsg}`);
            console.error('❌ API Error:', {
                endpoint: `${API_BASE}/ingestion/csv`,
                status: response.status,
                statusText: response.statusText,
                response: result
            });
        }
    } catch (e) {
        const errorDetails = `Backend connection failed: ${e.message}`;
        showError(errorDetails);
        console.error('❌ Network Error:', {
            endpoint: `${API_BASE}/ingestion/csv`,
            error: e,
            message: e.message,
            stack: e.stack
        });
    } finally {
        btn.innerText = "Start Ingestion Process";
        btn.disabled = false;
    }
}

function showSuccess(data) {
    document.getElementById('result-box').style.display = 'block';
    document.getElementById('error-box').style.display = 'none';

    console.log('✅ Upload Success:', data);

    const stats = data.statistics || {};
    document.getElementById('total-rows').innerText = stats.total_rows || '-';
    document.getElementById('tradable-rows').innerText = stats.tradable || '-';

    const avgWeight = stats.avg_learning_weight;
    document.getElementById('avg-weight').innerText = avgWeight !== undefined ? avgWeight.toFixed(2) : '-';

    // Update sidebar learning stats
    updateLearningSidebar(stats);

    fetchAuditLogs();
}

function updateLearningSidebar(stats) {
    // Update sidebar with learning data
    const totalCandles = stats.total_rows || 0;
    const learningCandles = stats.tradable || 0;
    const avgWeight = stats.avg_learning_weight || 0;

    document.getElementById('total-candles-sidebar').innerText = totalCandles.toLocaleString();
    document.getElementById('learning-candles-sidebar').innerText = learningCandles.toLocaleString();
    document.getElementById('avg-weight-sidebar').innerText = avgWeight.toFixed(2);

    // Add animation
    ['total-candles-sidebar', 'learning-candles-sidebar', 'avg-weight-sidebar'].forEach(id => {
        const el = document.getElementById(id);
        el.style.transform = 'scale(1.1)';
        el.style.transition = 'transform 0.3s ease';
        setTimeout(() => {
            el.style.transform = 'scale(1)';
        }, 300);
    });
}


function showError(msg) {
    document.getElementById('error-box').style.display = 'block';
    document.getElementById('result-box').style.display = 'none';
    document.getElementById('error-message').innerText = msg;
}

async function fetchAuditLogs() {
    const container = document.getElementById('audit-log-container');

    try {
        const response = await fetch(`${API_BASE}/ingestion/audit-log?limit=5`);
        const data = await response.json();

        if (data.status === 'success' && data.logs.length > 0) {
            container.innerHTML = data.logs.map(log => `
                <div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 0.9rem; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: var(--accent); font-weight: 600;">${log.asset} ${log.timeframe}</span>
                        <span style="color: #666;">${new Date(log.ingested_at).toLocaleString()}</span>
                    </div>
                    <div style="color: #888; margin-top: 4px;">Rows: ${log.total_rows} | Tradable: ${log.tradable_count} | Status: ${log.status}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: #555;">No recent audit records.</p>';
        }
    } catch (e) {
        container.innerHTML = '<p style="color: #555;">No recent audit records.</p>';
        console.error('❌ Audit Log Fetch Error:', {
            endpoint: `${API_BASE}/ingestion/audit-log`,
            error: e,
            message: e.message
        });
    }
}
