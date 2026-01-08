#!/bin/bash
# VERTICE - Google Cloud Run Deployment Script
# Deploys MCP Server, Backend, and Frontend to Cloud Run
# Account: juancs.d3v@gmail.com

set -e  # Exit on error

# ============================================
# Configuration
# ============================================
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"  # Set via env or change here
REGION="${GCP_REGION:-us-central1}"
ACCOUNT="juancs.d3v@gmail.com"

# Service names
MCP_SERVICE="vertice-mcp"
BACKEND_SERVICE="vertice-backend"
FRONTEND_SERVICE="vertice-frontend"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# Helper Functions
# ============================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# Pre-flight Checks
# ============================================
log_info "Running pre-flight checks..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" == "your-project-id" ]; then
    log_error "PROJECT_ID not set. Export GCP_PROJECT_ID environment variable or edit this script."
    echo "Usage: export GCP_PROJECT_ID=your-project-id && ./deploy-gcp.sh"
    exit 1
fi

log_success "Pre-flight checks passed"

# ============================================
# Authentication
# ============================================
log_info "Authenticating with GCP..."
gcloud auth login --account $ACCOUNT || {
    log_error "Authentication failed"
    exit 1
}

gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

log_success "Authenticated as $ACCOUNT"
log_success "Project set to $PROJECT_ID"

# ============================================
# Enable Required APIs
# ============================================
log_info "Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com \
    --project=$PROJECT_ID

log_success "APIs enabled"

# ============================================
# 1. Deploy MCP Server
# ============================================
log_info "=========================================="
log_info "STEP 1: Deploying MCP Server"
log_info "=========================================="

log_info "Building MCP Server Docker image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$MCP_SERVICE:latest \
    --file prometheus/Dockerfile \
    . || {
    log_error "MCP Server build failed"
    exit 1
}

log_success "MCP Server image built successfully"

log_info "Deploying MCP Server to Cloud Run..."
gcloud run deploy $MCP_SERVICE \
    --image gcr.io/$PROJECT_ID/$MCP_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 3000 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300s \
    --max-instances 10 \
    --concurrency 80 \
    --set-env-vars "MCP_HOST=0.0.0.0,MCP_PORT=3000,MCP_LOG_LEVEL=INFO" \
    --project=$PROJECT_ID || {
    log_error "MCP Server deployment failed"
    exit 1
}

MCP_URL=$(gcloud run services describe $MCP_SERVICE --region=$REGION --format='value(status.url)')
log_success "MCP Server deployed successfully!"
log_success "MCP Server URL: $MCP_URL"

# ============================================
# 2. Deploy Backend
# ============================================
log_info "=========================================="
log_info "STEP 2: Deploying Backend (FastAPI)"
log_info "=========================================="

log_info "Building Backend Docker image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest \
    vertice-chat-webapp/backend || {
    log_error "Backend build failed"
    exit 1
}

log_success "Backend image built successfully"

log_info "Deploying Backend to Cloud Run..."
gcloud run deploy $BACKEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 2 \
    --timeout 300s \
    --max-instances 20 \
    --concurrency 80 \
    --set-env-vars "MCP_SERVER_URL=$MCP_URL,MCP_CLIENT_TIMEOUT=30" \
    --project=$PROJECT_ID || {
    log_error "Backend deployment failed"
    exit 1
}

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format='value(status.url)')
log_success "Backend deployed successfully!"
log_success "Backend URL: $BACKEND_URL"

# ============================================
# 3. Deploy Frontend
# ============================================
log_info "=========================================="
log_info "STEP 3: Deploying Frontend (Next.js)"
log_info "=========================================="

log_info "Building Frontend Docker image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest \
    vertice-chat-webapp/frontend || {
    log_error "Frontend build failed"
    exit 1
}

log_success "Frontend image built successfully"

log_info "Deploying Frontend to Cloud Run..."
gcloud run deploy $FRONTEND_SERVICE \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 10 \
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL,NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1" \
    --project=$PROJECT_ID || {
    log_error "Frontend deployment failed"
    exit 1
}

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format='value(status.url)')
log_success "Frontend deployed successfully!"
log_success "Frontend URL: $FRONTEND_URL"

# ============================================
# Summary
# ============================================
echo ""
log_info "=========================================="
log_success "🎉 DEPLOYMENT COMPLETE!"
log_info "=========================================="
echo ""
echo -e "${GREEN}Services deployed:${NC}"
echo -e "  1. MCP Server:  ${BLUE}$MCP_URL${NC}"
echo -e "  2. Backend:     ${BLUE}$BACKEND_URL${NC}"
echo -e "  3. Frontend:    ${BLUE}$FRONTEND_URL${NC}"
echo ""
echo -e "${GREEN}Health checks:${NC}"
echo -e "  MCP:     curl $MCP_URL/health"
echo -e "  Backend: curl $BACKEND_URL/health"
echo -e "  Frontend: curl $FRONTEND_URL/api/health"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Test integration: curl $BACKEND_URL/api/v1/agents/execute"
echo -e "  2. Configure DNS for production domain"
echo -e "  3. Setup CI/CD pipeline"
echo -e "  4. Configure monitoring and alerting"
echo ""
log_success "Deployment script completed successfully!"
