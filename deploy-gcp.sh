#!/bin/bash

# VERTICE-CODE: SOVEREIGN DEPLOY SCRIPT (2026)
# Target Project: vertice-ai
# Stack: FastAPI (Cloud Run) + Next.js (Firebase Hosting)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID="vertice-ai"
REGION="us-central1"
BACKEND_SERVICE="vertice-backend"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}   VERTICE-CODE: DEPLOY MISSION START   ${NC}"
echo -e "${BLUE}============================================================${NC}"

# 1. Verification
echo -e "\n${YELLOW}[1/5] Verifying Environment...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set to: $PROJECT_ID${NC}"

# Enable Critical APIs
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    firebase.googleapis.com \
    --quiet

# 2. Backend Deploy (Cloud Run)
echo -e "\n${YELLOW}[2/5] Deploying Backend (FastAPI) to Cloud Run...${NC}"
cd vertice-chat-webapp/backend

# Create Artifact Registry if needed
gcloud artifacts repositories create vertice-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Vertice AI Docker Repository" \
    --quiet || true

echo "Building and Pushing Container..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/vertice-repo/$BACKEND_SERVICE:latest .

echo "Deploying to Cloud Run..."
gcloud run deploy $BACKEND_SERVICE \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/vertice-repo/$BACKEND_SERVICE:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars="ENVIRONMENT=production,PROJECT_ID=$PROJECT_ID" \
    --quiet

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✓ Backend Operational: $BACKEND_URL${NC}"
cd ../..

# 3. Frontend Sync
echo -e "\n${YELLOW}[3/5] Syncing Frontend with Backend...${NC}"
cat > vertice-chat-webapp/frontend/.env.production <<EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
NEXT_PUBLIC_FIREBASE_PROJECT_ID=$PROJECT_ID
NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$PROJECT_ID.firebaseapp.com
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$PROJECT_ID.appspot.com
EOF
echo -e "${GREEN}✓ Production environment variables generated${NC}"

# 4. Frontend Deploy (Firebase)
echo -e "\n${YELLOW}[4/5] Deploying Frontend (Next.js SSR)...${NC}"
cd vertice-chat-webapp/frontend

# Ensure pnpm is used for speed and consistency
echo "Installing dependencies..."
pnpm install

echo "Building production bundles..."
pnpm run build

echo "Deploying to Firebase Hosting..."
firebase deploy --only hosting --project $PROJECT_ID

cd ../..

# 5. Mission Success
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${GREEN}   MISSION COMPLETE: VERTICE IS LIVE   ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "Frontend URL: https://$PROJECT_ID.web.app"
echo -e "Backend URL:  $BACKEND_URL"
echo -e "\nNext Steps:"
echo -e "1. Add 'vertice-maximus.com' to Firebase Console"
echo -e "2. Update Cloudflare DNS records"
echo -e "${BLUE}============================================================${NC}"
