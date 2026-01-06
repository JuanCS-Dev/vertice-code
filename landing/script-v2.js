/*! Vertice-Code Landing v2.0 - Interactive Script */

// MCP Server URL
const MCP_URL = 'https://vertice-mcp-server-452089804714.us-central1.run.app/mcp';

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
    initMethodSelector();
    initTabSwitching();
});

// === METHOD SELECTOR ===
function initMethodSelector() {
    const methodSelect = document.getElementById('method-select');
    const requestInput = document.getElementById('request-input');

    if (!methodSelect || !requestInput) return;

    methodSelect.addEventListener('change', (e) => {
        const method = e.target.value;
        updateRequestTemplate(method);
    });
}

function updateRequestTemplate(method) {
    const requestInput = document.getElementById('request-input');
    if (!requestInput) return;

    const templates = {
        'tools/list': {
            jsonrpc: '2.0',
            method: 'tools/list',
            id: 'console-1'
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
            id: 'console-2'
        },
        'ping': {
            jsonrpc: '2.0',
            method: 'ping',
            id: 'console-3'
        }
    };

    const template = templates[method] || templates['tools/list'];
    requestInput.value = JSON.stringify(template, null, 2);
}

// === EXECUTE REQUEST ===
async function executeRequest() {
    const requestInput = document.getElementById('request-input');
    const responseOutput = document.getElementById('response-output');
    const responseMeta = document.getElementById('response-meta');
    const statusEl = document.getElementById('response-status');
    const timeEl = document.getElementById('response-time');

    if (!requestInput || !responseOutput) {
        console.error('Required elements not found');
        return;
    }

    // Validate JSON
    let requestData;
    try {
        requestData = JSON.parse(requestInput.value);
    } catch (error) {
        responseOutput.innerHTML = `<div class="placeholder" style="color: #ef4444;">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="24" cy="24" r="21"/>
                <path d="M15 15l18 18M33 15L15 33"/>
            </svg>
            <p>Invalid JSON</p>
            <p style="font-size: 0.875rem; opacity: 0.7;">${error.message}</p>
        </div>`;
        return;
    }

    // Show loading
    responseOutput.innerHTML = `<div class="placeholder">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="24" cy="24" r="21" opacity="0.25"/>
            <path d="M24 3a21 21 0 0121 21" stroke-linecap="round">
                <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="0 24 24"
                    to="360 24 24"
                    dur="1s"
                    repeatCount="indefinite"/>
            </path>
        </svg>
        <p>Executing request...</p>
    </div>`;

    const startTime = performance.now();

    try {
        const response = await fetch(MCP_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: requestInput.value
        });

        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        const data = await response.json();
        const jsonString = JSON.stringify(data, null, 2);

        responseOutput.innerHTML = `<pre style="margin: 0; font-family: var(--font-mono); font-size: 0.875rem;">${jsonString}</pre>`;

        // Show meta
        if (responseMeta && statusEl && timeEl) {
            responseMeta.style.display = 'flex';
            statusEl.textContent = response.ok ? '200 OK' : `${response.status} Error`;
            statusEl.style.color = response.ok ? '#10b981' : '#ef4444';
            timeEl.textContent = `${duration}ms`;
        }

    } catch (error) {
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        responseOutput.innerHTML = `<div class="placeholder" style="color: #ef4444;">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="24" cy="24" r="21"/>
                <path d="M15 15l18 18M33 15L15 33"/>
            </svg>
            <p>Connection Error</p>
            <p style="font-size: 0.875rem; opacity: 0.7;">${error.message}</p>
        </div>`;

        if (responseMeta && statusEl && timeEl) {
            responseMeta.style.display = 'flex';
            statusEl.textContent = 'Error';
            statusEl.style.color = '#ef4444';
            timeEl.textContent = `${duration}ms`;
        }
    }
}

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

// === COPY CODE ===
function copyCode(button) {
    const codeBlock = button.previousElementSibling;
    const code = codeBlock.querySelector('code').textContent;

    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.style.background = '#10b981';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// === SMOOTH SCROLL ===
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);

        if (targetElement) {
            const offsetTop = targetElement.offsetTop - 80;
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// === CONSOLE EASTER EGG ===
console.log(`
%c╔═══════════════════════════════════════╗
║                                       ║
║      VERTICE-CODE | AI AGENTS         ║
║                                       ║
║   Multi-LLM • 85+ Tools • MCP Ready   ║
║                                       ║
║        Soli Deo Gloria | 2026         ║
║                                       ║
╚═══════════════════════════════════════╝
`, 'color: #06b6d4; font-family: monospace; font-size: 14px; font-weight: bold;');

console.log('%c🚀 GitHub:', 'color: #10b981; font-size: 14px; font-weight: bold;');
console.log('%chttps://github.com/JuanCS-Dev/vertice-code', 'color: #60a5fa; font-size: 12px;');
