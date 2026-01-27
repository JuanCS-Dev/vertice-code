#!/bin/bash
set -e

# M5 Cutover Script - Vertice 2026
# Migrates traffic to Canonical Cloud Run Frontend (apps/web-console)
# Adheres to CODE_CONSTITUTION (Safety First, Sovereignty of Intent)

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
BACKEND_SERVICE="vertice-agent-gateway"

echo "--- M5 Cutover: Initializing Deployment for $PROJECT_ID ---"

# 1. Fetch Backend URL (Stable)
echo "Fetching Backend URL..."
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "Warning: Backend service '$BACKEND_SERVICE' not found. Using placeholder for build (Update env var later if needed)."
    BACKEND_URL="https://$BACKEND_SERVICE-$PROJECT_ID.a.run.app"
fi
echo "Backend URL: $BACKEND_URL"

# 2. Fetch Firebase Configuration
echo "Fetching Firebase SDK Config..."
FB_CONFIG=$(firebase apps:sdkconfig web --project $PROJECT_ID)

# Parse Config (Robust extraction)
API_KEY=$(echo "$FB_CONFIG" | grep "apiKey" | sed 's/.*"apiKey": "\(.*\)".*/\1/')
AUTH_DOMAIN=$(echo "$FB_CONFIG" | grep "authDomain" | sed 's/.*"authDomain": "\(.*\)".*/\1/')
FB_PROJECT_ID=$(echo "$FB_CONFIG" | grep "projectId" | sed 's/.*"projectId": "\(.*\)".*/\1/')
STORAGE_BUCKET=$(echo "$FB_CONFIG" | grep "storageBucket" | sed 's/.*"storageBucket": "\(.*\)".*/\1/')
MESSAGING_SENDER_ID=$(echo "$FB_CONFIG" | grep "messagingSenderId" | sed 's/.*"messagingSenderId": "\(.*\)".*/\1/')
APP_ID=$(echo "$FB_CONFIG" | grep "appId" | sed 's/.*"appId": "\(.*\)".*/\1/')

if [ -z "$API_KEY" ] || [ -z "$APP_ID" ]; then
    echo "CRITICAL ERROR: Failed to fetch Firebase Configuration."
    echo "Ensure you are authenticated with 'firebase login' and the project exists."
    exit 1
fi

echo "Firebase Config Loaded."

# 3. Trigger Cloud Build (The Canonical Pipeline)
echo "Submitting Cloud Build..."
echo "Config: cloudbuild.yaml"
echo "Substitutions being applied..."

# We use _API_URL to bake into the frontend build
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=\
_REGION="$REGION",\
_API_URL="$BACKEND_URL",\
_FIREBASE_API_KEY="$API_KEY",\
_FIREBASE_AUTH_DOMAIN="$AUTH_DOMAIN",\
_FIREBASE_PROJECT_ID="$FB_PROJECT_ID",\
_FIREBASE_STORAGE_BUCKET="$STORAGE_BUCKET",\
_FIREBASE_MESSAGING_SENDER_ID="$MESSAGING_SENDER_ID",\
_FIREBASE_APP_ID="$APP_ID" \
    .

echo "--- M5 Cutover: Deployment Triggered Successfully ---"
echo "Monitor the build logs above."
echo "Once complete, verify traffic at the Cloud Run Frontend URL."
