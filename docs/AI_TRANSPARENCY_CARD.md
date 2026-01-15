# 🇪🇺 AI TRANSPARENCY CARD (EU AI ACT COMPLIANCE)

**System Name:** Vertice Enterprise AI
**Provider:** Vertice-Code Inc.
**Date:** July 2026
**Compliance Status:** ✅ READY (Art. 13 & Art. 50 Compliant)

---

## 1. SYSTEM IDENTITY & PURPOSE
*   **Model Architecture:** Large Language Model (Google Gemini 1.5 Pro Foundation)
*   **Intended Use:** Software development assistance, code generation, refactoring, and technical reasoning.
*   **Risk Category:** **Limited Risk** (Transparency Obligations Apply). Not classified as "High Risk" under Annex III (not used for biometrics, critical infrastructure control without human-in-the-loop, or essential public services).

## 2. CAPABILITIES & LIMITATIONS
### ✅ Capabilities
*   **Code Generation:** Python, TypeScript, Go, Rust, and shell scripting.
*   **Architecture Analysis:** System design, security audits, and cloud infrastructure planning.
*   **Context Awareness:** Multi-file context retention up to 1M tokens.

### ⚠️ Limitations
*   **Hallucinations:** May generate syntactically correct but functionally incorrect code. Human review is **mandatory**.
*   **Knowledge Cutoff:** Knowledge base is static based on training data cutoff (early 2026), supplemented by RAG.
*   **Bias:** May reflect biases present in public code repositories used for pre-training.

## 3. DATA & PRIVACY (GDPR)
*   **Training Data:** Pre-trained by Google (Vertex AI). Vertice **DOES NOT** use customer data to train foundation models by default.
*   **RAG Usage:** Customer data is processed ephemerally for Retrieval-Augmented Generation within the specific tenant's isolated environment.
*   **Data Retention:** User prompts are retained for 30 days for abuse monitoring (unless Enterprise Zero-Retention is active) and then deleted.

## 4. HUMAN OVERSIGHT
*   **Code Review:** All AI-generated code must be reviewed and tested by a qualified human developer before deployment to production.
*   **Intervention:** Users can stop generation at any time.
*   **Feedback Mechanism:** Integrated "Flag Inaccurate Output" button for continuous RLHF tuning.

## 5. CONTENT PROVENANCE
*   **Watermarking:** All text outputs include `X-AI-Generated: true` headers.
*   **Credentials:** C2PA-compatible metadata is included in API responses via `X-Content-Provenance`.

---

*This document serves as the mandatory machine-readable disclosure required by the EU AI Act (2026).*
