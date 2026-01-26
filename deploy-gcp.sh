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
gcloud artifacts repositories create vertice-cloud \
    --repository-format=docker \
    --location=$REGION \
    --description="Vertice AI Docker Repository" \
    --quiet || true

echo "Building and Pushing Container..."
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/vertice-cloud/$BACKEND_SERVICE:latest .

echo "Deploying to Cloud Run..."
gcloud run deploy $BACKEND_SERVICE \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/vertice-cloud/$BACKEND_SERVICE:latest \
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
rm -f vertice-chat-webapp/frontend/.env* # Bulletproof: Remove potential conflict files

# Fetch Firebase Config dynamically
echo "Fetching Firebase Configuration..."
FIREBASE_CONFIG=$(firebase apps:sdkconfig web --project $PROJECT_ID)

# Extract values using simple grep/sed (avoiding jq dependency if possible, but jq is better if avail)
# Assuming standard output format from firebase CLI
API_KEY=$(echo "$FIREBASE_CONFIG" | grep "apiKey" | cut -d '"' -f 4)
AUTH_DOMAIN=$(echo "$FIREBASE_CONFIG" | grep "authDomain" | cut -d '"' -f 4)
STORAGE_BUCKET=$(echo "$FIREBASE_CONFIG" | grep "storageBucket" | cut -d '"' -f 4)
PROJECT_ID_FETCHED=$(echo "$FIREBASE_CONFIG" | grep "projectId" | cut -d '"' -f 4)

if [ -z "$API_KEY" ]; then
  echo -e "${RED}Error: Could not fetch Firebase API Key. Ensure a Web App is created in Firebase Console.${NC}"
  exit 1
fi

cat > vertice-chat-webapp/frontend/.env.production <<EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
NEXT_PUBLIC_FIREBASE_PROJECT_ID=$PROJECT_ID
NEXT_PUBLIC_FIREBASE_API_KEY=$API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$STORAGE_BUCKET
EOF
echo -e "${GREEN}✓ Production environment variables generated with REAL credentials${NC}"

# 4. Frontend Deploy (Firebase)
echo -e "\n${YELLOW}[4/5] Deploying Frontend (Next.js SSR)...${NC}"
cd vertice-chat-webapp/frontend

# Ensure clean slate for pnpm
echo "Cleaning dependencies..."
rm -rf node_modules package-lock.json .next

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
