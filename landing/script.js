/*! ============================================
    VERTICE-CODE LANDING PAGE SCRIPT
    Modern ES6+ | Smooth Animations | API Integration
    ============================================ */

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
    initSmoothScrolling();
    initTabSwitching();
    initScrollAnimations();
    initNavbarScroll();
    initMobileMenu();

    // Make API test function globally available
    window.testMCPServer = testMCPServer;
});

// === SMOOTH SCROLLING ===
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80;

                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });

                // Update active nav link
                updateActiveNavLink(targetId);
            }
        });
    });
}

// === TAB SWITCHING (API Demo) ===
function initTabSwitching() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.demo-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            // Remove active from all tabs
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active to clicked tab
            btn.classList.add('active');
            const targetContent = document.querySelector(`[data-content="${targetTab}"]`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

// === SCROLL ANIMATIONS ===
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards
    const cards = document.querySelectorAll('.feature-card, .agent-card, .tool-category, .perf-card, .governance-card, .tech-card');

    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
}

// === NAVBAR SCROLL BEHAVIOR ===
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

    // Change navbar background on scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(10, 14, 26, 0.95)';
        } else {
            navbar.style.background = 'rgba(10, 14, 26, 0.8)';
        }

        // Update active nav link based on scroll position
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;

            if (window.scrollY >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        updateActiveNavLink(current);
    });
}

function updateActiveNavLink(sectionId) {
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
        }
    });
}

// === MOBILE MENU (Optional - for future hamburger menu) ===
function initMobileMenu() {
    // Placeholder for mobile menu implementation
    // Can be expanded later if needed
}

// === MCP SERVER API TEST ===
async function testMCPServer() {
    const responseDiv = document.getElementById('apiResponse');
    const responseBody = responseDiv.querySelector('.response-body');
    const testBtn = document.querySelector('.btn-test-api');

    if (!responseDiv || !testBtn) {
        console.error('API response elements not found');
        return;
    }

    // Show loading state
    testBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="8" cy="8" r="6" opacity="0.25"/>
            <path d="M8 2a6 6 0 016 6" stroke-linecap="round">
                <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="0 8 8"
                    to="360 8 8"
                    dur="1s"
                    repeatCount="indefinite"/>
            </path>
        </svg>
        Testando...
    `;
    testBtn.disabled = true;

    responseDiv.style.display = 'block';
    responseBody.textContent = 'Enviando requisição ao MCP Server...';

    try {
        const response = await fetch('https://vertice-mcp-server-452089804714.us-central1.run.app/mcp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'test',
                id: 'landing-page-demo'
            })
        });

        if (response.ok) {
            const data = await response.json();
            responseBody.textContent = JSON.stringify(data, null, 2);

            // Add success styling
            responseDiv.style.borderColor = '#10b981';
            responseDiv.querySelector('.response-header').style.color = '#10b981';
        } else {
            const errorText = await response.text();
            responseBody.textContent = `❌ Erro ${response.status}: ${response.statusText}\n\n${errorText}`;

            // Add error styling
            responseDiv.style.borderColor = '#ef4444';
            responseDiv.querySelector('.response-header').style.color = '#ef4444';
        }
    } catch (error) {
        responseBody.textContent = `❌ Erro de conexão:\n${error.message}\n\nVerifique:\n- O MCP Server está rodando?\n- Há problemas de CORS?\n- A URL está correta?`;

        // Add error styling
        responseDiv.style.borderColor = '#ef4444';
        responseDiv.querySelector('.response-header').style.color = '#ef4444';
    } finally {
        // Reset button
        testBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 15 8 5 13 5 3"/>
            </svg>
            Test API
        `;
        testBtn.disabled = false;
    }
}

// === COPY CODE TO CLIPBOARD (Optional Enhancement) ===
function initCodeCopy() {
    const codeBlocks = document.querySelectorAll('.code-block');

    codeBlocks.forEach(block => {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn-copy-code';
        copyBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="4" y="4" width="8" height="10" rx="1"/>
                <path d="M6 4V2a1 1 0 011-1h6a1 1 0 011 1v10a1 1 0 01-1 1h-2"/>
            </svg>
        `;
        copyBtn.title = 'Copy code';

        copyBtn.addEventListener('click', async () => {
            const code = block.querySelector('code').textContent;

            try {
                await navigator.clipboard.writeText(code);

                copyBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M13 4L6 11L3 8"/>
                    </svg>
                `;

                setTimeout(() => {
                    copyBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="4" y="4" width="8" height="10" rx="1"/>
                            <path d="M6 4V2a1 1 0 011-1h6a1 1 0 011 1v10a1 1 0 01-1 1h-2"/>
                        </svg>
                    `;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
            }
        });

        block.style.position = 'relative';
        block.appendChild(copyBtn);
    });
}

// === PERFORMANCE METRICS (Optional - Real-time stats) ===
function initPerformanceMetrics() {
    // Placeholder for real-time MCP server metrics
    // Can be expanded to fetch actual metrics from /health endpoint
}

// === EASTER EGG: Konami Code ===
function initKonamiCode() {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;

    document.addEventListener('keydown', (e) => {
        if (e.key === konamiCode[konamiIndex]) {
            konamiIndex++;

            if (konamiIndex === konamiCode.length) {
                // Easter egg activated!
                document.body.style.animation = 'rainbow 2s infinite';
                console.log('🚀 PROMETHEUS ACTIVATED! You found the Easter egg!');
                konamiIndex = 0;
            }
        } else {
            konamiIndex = 0;
        }
    });
}

// === UTILITY FUNCTIONS ===

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Get query parameters
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};

    for (const [key, value] of params) {
        result[key] = value;
    }

    return result;
}

// === AUTO-SCROLL TO SECTION FROM URL ===
window.addEventListener('load', () => {
    const hash = window.location.hash;

    if (hash) {
        setTimeout(() => {
            const targetElement = document.querySelector(hash);
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        }, 100);
    }
});

// === EXPORT FOR EXTERNAL USE ===
window.VerticeCode = {
    testMCPServer,
    initSmoothScrolling,
    initTabSwitching,
    initScrollAnimations,
    initNavbarScroll
};

// === CONSOLE EASTER EGG ===
console.log(`
%c╔═══════════════════════════════════════╗
║                                       ║
║      VERTICE-CODE | IA COLETIVA       ║
║                                       ║
║    20 Agentes • 85 Ferramentas        ║
║    MCP Server Live • Prometheus L4    ║
║                                       ║
║        Soli Deo Gloria | 2026         ║
║                                       ║
╚═══════════════════════════════════════╝
`, 'color: #3b82f6; font-family: monospace; font-size: 14px; font-weight: bold;');

console.log('%c🚀 Open Source? Check us out:', 'color: #06b6d4; font-size: 14px; font-weight: bold;');
console.log('%chttps://github.com/JuanCS-Dev/vertice-code', 'color: #60a5fa; font-size: 12px;');
console.log('%c🔥 MCP Server Live:', 'color: #10b981; font-size: 14px; font-weight: bold;');
console.log('%chttps://vertice-mcp-server-452089804714.us-central1.run.app/', 'color: #60a5fa; font-size: 12px;');
