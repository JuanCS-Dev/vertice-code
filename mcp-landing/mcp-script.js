/*! ============================================
    VERTICE MCP SERVER LANDING - INTERACTIVE JS
    Real-time API testing with love ❤️
    ============================================ */

// MCP Server URL
const MCP_URL = 'https://vertice-mcp-server-452089804714.us-central1.run.app';

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
    initTabSwitching();
    initRequestBuilder();
    checkServerHealth();
    updateUptime();

    // Auto-update every 30 seconds
    setInterval(checkServerHealth, 30000);
    setInterval(updateUptime, 1000);
});

// === TAB SWITCHING ===
function initTabSwitching() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const codeExamples = document.querySelectorAll('.code-example');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            codeExamples.forEach(c => c.classList.remove('active'));

            // Add active to clicked
            btn.classList.add('active');
            const targetExample = document.querySelector(`[data-content="${targetTab}"]`);
            if (targetExample) {
                targetExample.classList.add('active');
            }
        });
    });
}

// === REQUEST BUILDER ===
function initRequestBuilder() {
    const methodSelect = document.getElementById('method-select');
    const requestJson = document.getElementById('request-json');

    if (!methodSelect || !requestJson) return;

    methodSelect.addEventListener('change', (e) => {
        const method = e.target.value;
        updateRequestJson(method);
    });
}

function updateRequestJson(method) {
    const requestJson = document.getElementById('request-json');
    if (!requestJson) return;

    const templates = {
        'tools/list': {
            jsonrpc: '2.0',
            method: 'tools/list',
            id: 'playground-test-1'
        },
        'tools/call': {
            jsonrpc: '2.0',
            method: 'tools/call',
            params: {
                name: 'read_file',
                arguments: {
                    path: '/path/to/file.txt'
                }
            },
            id: 'playground-test-2'
        },
        'ping': {
            jsonrpc: '2.0',
            method: 'ping',
            id: 'playground-test-3'
        }
    };

    const template = templates[method] || templates['tools/list'];
    requestJson.value = JSON.stringify(template, null, 2);
}

// === TEST MCP ENDPOINT ===
async function testMCPEndpoint() {
    const responseContainer = document.getElementById('response-container');
    const responseMeta = document.getElementById('response-meta');

    if (!responseContainer) {
        console.error('Response container not found');
        return;
    }

    // Show loading
    responseContainer.innerHTML = `
        <div class="response-placeholder">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="32" cy="32" r="28" opacity="0.25"/>
                <path d="M32 4a28 28 0 0128 28" stroke-linecap="round">
                    <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 32 32"
                        to="360 32 32"
                        dur="1s"
                        repeatCount="indefinite"/>
                </path>
            </svg>
            <p>Testing MCP endpoint...</p>
        </div>
    `;

    const startTime = performance.now();

    try {
        const response = await fetch(`${MCP_URL}/mcp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'tools/list',
                id: 'landing-test-1'
            })
        });

        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        const data = await response.json();
        const jsonString = JSON.stringify(data, null, 2);

        responseContainer.innerHTML = `<pre>${jsonString}</pre>`;

        // Show meta
        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = response.ok ? '200 OK' : `${response.status} Error`;
            document.getElementById('response-status').style.color = response.ok ? 'var(--success)' : 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = `${jsonString.length} bytes`;
        }

    } catch (error) {
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        responseContainer.innerHTML = `
            <div class="response-placeholder" style="color: var(--danger);">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="32" cy="32" r="28"/>
                    <path d="M20 20l24 24M44 20L20 44"/>
                </svg>
                <p>❌ Error: ${error.message}</p>
                <p style="font-size: 0.875rem; opacity: 0.7;">Check CORS settings or server availability</p>
            </div>
        `;

        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = 'Error';
            document.getElementById('response-status').style.color = 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = '--';
        }
    }
}

// === TEST HEALTH ENDPOINT ===
async function testHealthEndpoint() {
    const responseContainer = document.getElementById('response-container');
    const responseMeta = document.getElementById('response-meta');

    if (!responseContainer) {
        console.error('Response container not found');
        return;
    }

    responseContainer.innerHTML = `
        <div class="response-placeholder">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="32" cy="32" r="28" opacity="0.25"/>
                <path d="M32 4a28 28 0 0128 28" stroke-linecap="round">
                    <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 32 32"
                        to="360 32 32"
                        dur="1s"
                        repeatCount="indefinite"/>
                </path>
            </svg>
            <p>Checking server health...</p>
        </div>
    `;

    const startTime = performance.now();

    try {
        const response = await fetch(`${MCP_URL}/health`);
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        const data = await response.json();
        const jsonString = JSON.stringify(data, null, 2);

        responseContainer.innerHTML = `<pre>${jsonString}</pre>`;

        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = response.ok ? '200 OK' : `${response.status} Error`;
            document.getElementById('response-status').style.color = response.ok ? 'var(--success)' : 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = `${jsonString.length} bytes`;
        }

        // Update latency in hero
        const latencyElement = document.getElementById('latency');
        if (latencyElement) {
            latencyElement.textContent = `${duration}ms`;
        }

    } catch (error) {
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        responseContainer.innerHTML = `
            <div class="response-placeholder" style="color: var(--danger);">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="32" cy="32" r="28"/>
                    <path d="M20 20l24 24M44 20L20 44"/>
                </svg>
                <p>❌ Error: ${error.message}</p>
                <p style="font-size: 0.875rem; opacity: 0.7;">Server may be offline</p>
            </div>
        `;

        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = 'Error';
            document.getElementById('response-status').style.color = 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = '--';
        }
    }
}

// === EXECUTE CUSTOM REQUEST ===
async function executeRequest() {
    const requestJson = document.getElementById('request-json');
    const responseContainer = document.getElementById('response-container');
    const responseMeta = document.getElementById('response-meta');

    if (!requestJson || !responseContainer) {
        console.error('Required elements not found');
        return;
    }

    let requestData;
    try {
        requestData = JSON.parse(requestJson.value);
    } catch (error) {
        responseContainer.innerHTML = `
            <div class="response-placeholder" style="color: var(--danger);">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="32" cy="32" r="28"/>
                    <path d="M20 20l24 24M44 20L20 44"/>
                </svg>
                <p>❌ Invalid JSON</p>
                <p style="font-size: 0.875rem; opacity: 0.7;">${error.message}</p>
            </div>
        `;
        return;
    }

    responseContainer.innerHTML = `
        <div class="response-placeholder">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="32" cy="32" r="28" opacity="0.25"/>
                <path d="M32 4a28 28 0 0128 28" stroke-linecap="round">
                    <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 32 32"
                        to="360 32 32"
                        dur="1s"
                        repeatCount="indefinite"/>
                </path>
            </svg>
            <p>Executing request...</p>
        </div>
    `;

    const startTime = performance.now();

    try {
        const response = await fetch(`${MCP_URL}/mcp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: requestJson.value
        });

        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        const data = await response.json();
        const jsonString = JSON.stringify(data, null, 2);

        responseContainer.innerHTML = `<pre>${jsonString}</pre>`;

        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = response.ok ? '200 OK' : `${response.status} Error`;
            document.getElementById('response-status').style.color = response.ok ? 'var(--success)' : 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = `${jsonString.length} bytes`;
        }

    } catch (error) {
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        responseContainer.innerHTML = `
            <div class="response-placeholder" style="color: var(--danger);">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="32" cy="32" r="28"/>
                    <path d="M20 20l24 24M44 20L20 44"/>
                </svg>
                <p>❌ Error: ${error.message}</p>
                <p style="font-size: 0.875rem; opacity: 0.7;">Check request format and server status</p>
            </div>
        `;

        if (responseMeta) {
            responseMeta.style.display = 'flex';
            document.getElementById('response-status').textContent = 'Error';
            document.getElementById('response-status').style.color = 'var(--danger)';
            document.getElementById('response-time').textContent = `${duration}ms`;
            document.getElementById('response-size').textContent = '--';
        }
    }
}

// === CLEAR PLAYGROUND ===
function clearPlayground() {
    const requestJson = document.getElementById('request-json');
    const responseContainer = document.getElementById('response-container');
    const responseMeta = document.getElementById('response-meta');

    if (requestJson) {
        requestJson.value = JSON.stringify({
            jsonrpc: '2.0',
            method: 'tools/list',
            id: 'playground-test-1'
        }, null, 2);
    }

    if (responseContainer) {
        responseContainer.innerHTML = `
            <div class="response-placeholder">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="8" y="8" width="48" height="48" rx="4"/>
                    <path d="M16 24h32M16 32h32M16 40h20"/>
                </svg>
                <p>Execute a request to see the response here</p>
            </div>
        `;
    }

    if (responseMeta) {
        responseMeta.style.display = 'none';
    }
}

// === CHECK SERVER HEALTH (Background) ===
async function checkServerHealth() {
    try {
        const startTime = performance.now();
        const response = await fetch(`${MCP_URL}/health`);
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        const latencyElement = document.getElementById('latency');
        if (latencyElement && response.ok) {
            latencyElement.textContent = `${duration}ms`;
        }

    } catch (error) {
        console.error('Health check failed:', error);
        const latencyElement = document.getElementById('latency');
        if (latencyElement) {
            latencyElement.textContent = 'Offline';
            latencyElement.style.color = 'var(--danger)';
        }
    }
}

// === UPDATE UPTIME ===
function updateUptime() {
    const uptimeElement = document.getElementById('uptime');
    if (!uptimeElement) return;

    // Simulated uptime (you can replace with real server uptime)
    const startDate = new Date('2026-01-01T00:00:00Z');
    const now = new Date();
    const diff = now - startDate;

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (days > 0) {
        uptimeElement.textContent = `${days}d ${hours}h`;
    } else {
        uptimeElement.textContent = `${hours}h`;
    }
}

// === CONSOLE EASTER EGG ===
console.log(`
%c╔═══════════════════════════════════════╗
║                                       ║
║     VERTICE MCP SERVER | LIVE         ║
║                                       ║
║   Model Context Protocol v1.0         ║
║   85+ Tools • Multi-LLM • Cloud Run   ║
║                                       ║
║        Made with Love ❤️ | 2026        ║
║                                       ║
╚═══════════════════════════════════════╝
`, 'color: #06b6d4; font-family: monospace; font-size: 14px; font-weight: bold;');

console.log('%c🚀 MCP Server Live:', 'color: #10b981; font-size: 14px; font-weight: bold;');
console.log('%c' + MCP_URL, 'color: #60a5fa; font-size: 12px;');
console.log('%c💡 Try the playground to test the API!', 'color: #06b6d4; font-size: 12px;');
