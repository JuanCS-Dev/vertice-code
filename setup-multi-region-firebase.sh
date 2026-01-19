#!/bin/bash
# Multi-Region Firebase App Hosting Setup for Vertice Enterprise
# Sets up Firebase backends in US, EU, and Asia regions

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"
echo "🚀 Setting up multi-region Firebase App Hosting for project: $PROJECT_ID"

# ============================================
# Region Configurations
# ============================================
declare -A REGIONS=(
    ["us-central1"]="vertice-us"
    ["europe-west1"]="vertice-eu"
    ["asia-southeast1"]="vertice-asia"
)

# ============================================
# Function to setup Firebase backend for a region
# ============================================
setup_firebase_backend() {
    local region=$1
    local backend_id=$2

    echo "📍 Setting up Firebase App Hosting backend for $region..."

    # Create App Hosting backend
    echo "Creating App Hosting backend: $backend_id in $region"
    firebase apphosting:backends:create \
        --backend $backend_id \
        --project $PROJECT_ID \
        --primary-region $region

    # Backend configured automatically during creation
    echo "✅ Backend $backend_id configured automatically"

    echo "✅ Firebase backend $backend_id ready in $region"
}

# ============================================
# Main Setup Process
# ============================================

echo "🔧 Initializing Firebase project..."
firebase use $PROJECT_ID

# Setup each region
for region in "${!REGIONS[@]}"; do
    backend_id="${REGIONS[$region]}"
    setup_firebase_backend "$region" "$backend_id"
done

echo ""
echo "🎉 Multi-region Firebase setup complete!"
echo ""
echo "📋 Summary of deployed backends:"
for region in "${!REGIONS[@]}"; do
    backend_id="${REGIONS[$region]}"
    echo "  • $region: $backend_id"
done

echo ""
echo "🔄 Next steps:"
echo "  1. Update your DNS/load balancer to route traffic to appropriate backends"
echo "  2. Set up Firebase custom domains for each region:"
echo "     firebase hosting:sites:add-domains $PROJECT_ID us.vertice-maximus.com"
echo "     firebase hosting:sites:add-domains $PROJECT_ID eu.vertice-maximus.com"
echo "     firebase hosting:sites:add-domains $PROJECT_ID asia.vertice-maximus.com"
echo "  3. Configure traffic splitting or geo-routing in your CDN"
echo ""
echo "📊 Monitor deployment status:"
echo "  firebase apphosting:backends:list --project $PROJECT_ID"
