document.addEventListener('DOMContentLoaded', () => {
    
    // --- CONSOLE LOGIC ---
    
    const requestEditor = document.getElementById('request-editor');
    const responseViewer = document.getElementById('response-viewer');
    const executeBtn = document.getElementById('execute-btn');
    const methodSelect = document.getElementById('method-select');
    const timingBadge = document.getElementById('timing-badge');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    const MOCK_RESPONSES = {
        'list': {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "read_file", "description": "Read file content"},
                    {"name": "write_file", "description": "Write content to file"},
                    {"name": "git_commit", "description": "Create a git commit"},
                    {"name": "run_shell", "description": "Execute shell command"},
                    {"name": "search_web", "description": "Search the internet"}
                ],
                "agents": [
                    {"role": "orchestrator", "status": "active"},
                    {"role": "coder", "status": "idle"},
                    {"role": "reviewer", "status": "idle"}
                ]
            },
            "id": 1
        },
        'call': {
            "jsonrpc": "2.0",
            "result": {
                "content": "Analyzing project structure...\nFound 20 agents and 85 tools.\nSystem is operational.",
                "usage": {"tokens": 145, "cost": "$0.002"}
            },
            "id": 1
        },
        'ping': {
            "jsonrpc": "2.0",
            "result": "pong",
            "id": 1
        }
    };

    const TEMPLATES = {
        'list': '{\n  "jsonrpc": "2.0",\n  "method": "tools/list",\n  "id": 1\n}',
        'call': '{\n  "jsonrpc": "2.0",\n  "method": "tools/call",\n  "params": {\n    "name": "analyze_project",\n    "args": { "path": "." }\n  },\n  "id": 1\n}',
        'ping': '{\n  "jsonrpc": "2.0",\n  "method": "ping",\n  "id": 1\n}'
    };

    // Method Selector Logic
    methodSelect.addEventListener('change', (e) => {
        const method = e.target.value;
        requestEditor.value = TEMPLATES[method];
        responseViewer.textContent = '// Ready to execute...';
        responseViewer.classList.add('text-muted');
        responseViewer.classList.remove('text-green-400');
        timingBadge.classList.add('hidden');
    });

    // Execute Logic
    executeBtn.addEventListener('click', async () => {
        const method = methodSelect.value;
        const responseData = MOCK_RESPONSES[method];
        
        // UI State: Loading
        executeBtn.disabled = true;
        executeBtn.innerHTML = `<svg class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Running...`;
        responseViewer.textContent = '';
        responseViewer.classList.remove('text-muted');
        responseViewer.classList.add('text-green-400');
        
        statusIndicator.className = "w-2 h-2 rounded-full bg-yellow-500 animate-pulse";
        statusText.textContent = "Processing...";

        // Simulate Network Latency (random 300-800ms)
        const latency = Math.floor(Math.random() * 500) + 300;
        await new Promise(r => setTimeout(r, latency));

        // UI State: Success
        executeBtn.disabled = false;
        executeBtn.innerHTML = `<span>Execute</span><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>`;
        
        statusIndicator.className = "w-2 h-2 rounded-full bg-green-500";
        statusText.textContent = "Connected: Vertice-MCP";

        timingBadge.textContent = `${latency}ms`;
        timingBadge.classList.remove('hidden');

        // Stream Response (Typewriter Effect)
        const jsonString = JSON.stringify(responseData, null, 2);
        let i = 0;
        const speed = 5; // ms per char

        function typeWriter() {
            if (i < jsonString.length) {
                responseViewer.textContent += jsonString.charAt(i);
                i++;
                responseViewer.scrollTop = responseViewer.scrollHeight;
                setTimeout(typeWriter, speed);
            } else {
                // Syntax Highlight (Simple Regex) after typing
                highlightSyntax(responseViewer);
            }
        }
        typeWriter();
    });

    function highlightSyntax(element) {
        // Very basic syntax highlighting for demo purposes
        // In production, use Prism.js or Highlight.js
        let html = element.innerHTML;
        html = html.replace(/"(.*?) ":/g, '<span class="key">"$1"</span>:');
        html = html.replace(/: "(.*?)"/g, ': <span class="string">"$1"</span>');
        html = html.replace(/: (\d+)/g, ': <span class="number">$1</span>');
        html = html.replace(/: (true|false)/g, ': <span class="boolean">$1</span>');
        element.innerHTML = html;
    }

    // --- SMOOTH SCROLL & OBSERVER ---
    
    // Intersection Observer for fade-in animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-reveal');
                entry.target.classList.remove('opacity-0'); // Ensure visibility
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('section').forEach(section => {
        section.classList.add('opacity-0'); // Initial state
        observer.observe(section);
    });

    // Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // --- SCROLL TO CONSOLE HELPER ---
    window.scrollToConsole = function() {
        document.getElementById('console').scrollIntoView({ behavior: 'smooth' });
    };
});
