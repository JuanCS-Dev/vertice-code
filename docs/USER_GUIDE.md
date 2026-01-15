# 📖 VERTICE CODE USER GUIDE
**Version:** 1.0.0-RC1
**Date:** 2026-01-14

---

## 🌟 Introduction
Welcome to **Vertice**, the Collective AI Platform.
This guide covers the three pillars of the Vertice Code system:
1.  **Web App (SaaS)**: For team collaboration.
2.  **TUI (Terminal UI)**: For usage in developer environments.
3.  **CLI (Command Line)**: For automation and headless tasks.

---

## 🚀 Quick Start

### 1. Web App (SaaS)
*   **URL:** `https://vertice-app.com` (Fake Staging URL for now)
*   **Login:** Sign in with Google.
*   **Billing:** Dashboard -> Billing -> Subscribe to Pro ($29/mo).

### 2. Vertice TUI (Terminal)
The ultimate developer experience.
```bash
pip install vertice-code
vertice
```
*   **Controls:** Mouse supported. `Ctrl+Q` to quit.
*   **Features:** Multi-Agent Chat, File Editing, System Status.

### 3. Vertice CLI (Automation)
Run headless tasks directly from your shell.
```bash
# Analyze a file
vertice -p "Analyze src/main.py for bugs"

# Run the Prometheus Meta-Agent (Evolution Loop)
python -m prometheus "Improve the documentation"
```

---

## 🔐 Security & Multi-Tenancy
Vertice is "Blindado" (Shielded) by default.

*   **Tenants:** Your data is isolated in a unique `tenant-{uuid}` container.
*   **Zero-Trust:** Every request verifies `Authorization: Bearer <token>`.
*   **Revocation:** Logging out invalidates tokens globally instantly.

---

## 🛠 Troubleshooting
**Issue:** `404 Publisher Model Not Found`
**Fix:** Ensure you have access to `us-central1` and run:
```bash
gcloud auth application-default login
```

**Issue:** TUI doesn't render
**Fix:** Ensure your terminal supports truecolor (Use iTerm2, Alacritty, or VSCode Terminal).

---

*Operando sob a Constituição Vértice v3.0*
