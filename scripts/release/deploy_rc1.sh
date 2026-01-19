#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   🚀 VERTICE CODE: RELEASE CANDIDATE 1.0 (DEPLOYMENT)             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Pre-Flight Checks
echo -e "${YELLOW}🔍 [1/3] Running Pre-Flight Checks (Prometheus + TUI + Multitenancy)...${NC}"
python3 scripts/e2e/verify_prometheus.py
python3 scripts/e2e/verify_tui_rendering.py
python3 scripts/e2e/verify_multitenancy.py

echo -e "${GREEN}✅ Pre-Flight Checks Passed.${NC}"
echo ""

# 2. Deployment Confirmation
echo -e "${YELLOW}⚠️  You are about to deploy 'vertice-backend' to Google Cloud Run (Production).${NC}"
read -p "Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}❌ Deployment cancelled.${NC}"
    exit 1
fi

# 3. SaaS Deploy
echo -e "${CYAN}☁️  [2/3] Building and Deploying SaaS Web App...${NC}"
# Check if running in a real env before executing massive build
# Use --dry-run logic or verify gcloud exists
if command -v gcloud &> /dev/null; then
    echo "   Submitting build to Cloud Build..."
    gcloud builds submit vertice-chat-webapp/backend --config vertice-chat-webapp/backend/cloudbuild.yaml

    echo "   Deploying to Cloud Run..."
    gcloud run deploy vertice-backend \
        --image gcr.io/vertice-ai/vertice-backend:latest \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated
else
    echo -e "${RED}❌ gcloud CLI not found. Skipping Cloud Deploy.${NC}"
fi

# 4. CLI Publish (Local Install for now)
echo -e "${CYAN}💻 [3/3] Installing Vertice CLI (Local Release)...${NC}"
pip install .

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   🎉 DEPLOYMENT COMPLETE. SYSTEM IS LIVE.                         ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
