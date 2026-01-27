#!/bin/bash
# =============================================================================
# DIGITAL NERVOUS SYSTEM - DEPLOYMENT SCRIPT
# =============================================================================
#
# Deploys the complete Nervous System infrastructure to GCP:
# - Creates Eventarc triggers
# - Sets up Pub/Sub topics
# - Configures Cloud Monitoring alerts
# - Enables required APIs
#
# Usage: ./deploy-nervous-system.sh [--dry-run] [--destroy]
#
# Prerequisites:
# - gcloud CLI authenticated
# - Project ID set (gcloud config set project vertice-ai)
# - Required APIs enabled
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-vertice-ai}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_NAME="vertice-agent-gateway"
SERVICE_ACCOUNT_NAME="nervous-system-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
DESTROY=false
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --destroy)
            DESTROY=true
            ;;
    esac
done

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $*"
    else
        "$@"
    fi
}

# =============================================================================
# DESTROY MODE
# =============================================================================

if [ "$DESTROY" = true ]; then
    log_warn "🗑️  Destroying Nervous System infrastructure..."

    # Delete Eventarc triggers
    log_info "Deleting Eventarc triggers..."
    run_cmd gcloud eventarc triggers delete nervous-system-logging \
        --location="$REGION" --quiet 2>/dev/null || true
    run_cmd gcloud eventarc triggers delete nervous-system-monitoring \
        --location="$REGION" --quiet 2>/dev/null || true
    run_cmd gcloud eventarc triggers delete nervous-system-pubsub \
        --location="$REGION" --quiet 2>/dev/null || true

    # Delete Pub/Sub topics
    log_info "Deleting Pub/Sub topics..."
    run_cmd gcloud pubsub topics delete nervous-system-events --quiet 2>/dev/null || true
    run_cmd gcloud pubsub topics delete nervous-system-alerts --quiet 2>/dev/null || true
    run_cmd gcloud pubsub topics delete nervous-system-escalations --quiet 2>/dev/null || true
    run_cmd gcloud pubsub topics delete nervous-system-dlq --quiet 2>/dev/null || true

    # Delete service account
    log_info "Deleting service account..."
    run_cmd gcloud iam service-accounts delete "$SERVICE_ACCOUNT_EMAIL" --quiet 2>/dev/null || true

    log_success "🧹 Nervous System infrastructure destroyed"
    exit 0
fi

# =============================================================================
# DEPLOY MODE
# =============================================================================

echo ""
echo "🧬 =================================================================="
echo "   DIGITAL NERVOUS SYSTEM - DEPLOYMENT"
echo "   Project: $PROJECT_ID"
echo "   Region:  $REGION"
echo "   Service: $SERVICE_NAME"
echo "🧬 =================================================================="
echo ""

# Step 1: Enable required APIs
log_info "Step 1: Enabling required APIs..."
APIS=(
    "eventarc.googleapis.com"
    "pubsub.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
)

for api in "${APIS[@]}"; do
    run_cmd gcloud services enable "$api" --project="$PROJECT_ID" --quiet
done
log_success "APIs enabled"

# Step 2: Create Service Account
log_info "Step 2: Creating service account..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
    run_cmd gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Digital Nervous System Service Account" \
        --description="Service account for NEXUS Digital Nervous System" \
        --project="$PROJECT_ID"
    log_success "Service account created: $SERVICE_ACCOUNT_EMAIL"
else
    log_info "Service account already exists"
fi

# Step 3: Grant IAM permissions
log_info "Step 3: Granting IAM permissions..."
ROLES=(
    "roles/run.invoker"
    "roles/logging.logWriter"
    "roles/logging.viewer"
    "roles/monitoring.metricWriter"
    "roles/monitoring.viewer"
    "roles/pubsub.subscriber"
    "roles/pubsub.publisher"
    "roles/eventarc.eventReceiver"
)

for role in "${ROLES[@]}"; do
    run_cmd gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet 2>/dev/null || true
done
log_success "IAM permissions granted"

# Step 4: Create Pub/Sub topics
log_info "Step 4: Creating Pub/Sub topics..."
TOPICS=(
    "nervous-system-events"
    "nervous-system-alerts"
    "nervous-system-escalations"
    "nervous-system-dlq"
)

for topic in "${TOPICS[@]}"; do
    if ! gcloud pubsub topics describe "$topic" --project="$PROJECT_ID" &>/dev/null; then
        run_cmd gcloud pubsub topics create "$topic" \
            --project="$PROJECT_ID" \
            --message-retention-duration="7d" \
            --labels="component=nervous-system"
        log_success "Created topic: $topic"
    else
        log_info "Topic already exists: $topic"
    fi
done

# Step 5: Get Cloud Run service URL
log_info "Step 5: Getting Cloud Run service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    log_error "Cloud Run service '$SERVICE_NAME' not found in $REGION"
    log_info "Please deploy the agent-gateway first"
    exit 1
fi
log_success "Service URL: $SERVICE_URL"

# Step 6: Create Eventarc triggers
log_info "Step 6: Creating Eventarc triggers..."

# Get project number for default compute service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# Trigger for Cloud Audit Logs
log_info "Creating Cloud Audit Log trigger..."
if ! gcloud eventarc triggers describe nervous-system-logging --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    run_cmd gcloud eventarc triggers create nervous-system-logging \
        --location="$REGION" \
        --destination-run-service="$SERVICE_NAME" \
        --destination-run-region="$REGION" \
        --destination-run-path="/v1/nexus/v1/eventarc/logging" \
        --event-filters="type=google.cloud.audit.log.v1.written" \
        --event-filters="serviceName=run.googleapis.com" \
        --service-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$PROJECT_ID"
    log_success "Created logging trigger"
else
    log_info "Logging trigger already exists"
fi

# Trigger for Pub/Sub (nervous-system-events topic)
log_info "Creating Pub/Sub events trigger..."
if ! gcloud eventarc triggers describe nervous-system-pubsub --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    run_cmd gcloud eventarc triggers create nervous-system-pubsub \
        --location="$REGION" \
        --destination-run-service="$SERVICE_NAME" \
        --destination-run-region="$REGION" \
        --destination-run-path="/v1/nexus/v1/eventarc/pubsub" \
        --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
        --transport-topic="projects/$PROJECT_ID/topics/nervous-system-events" \
        --service-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$PROJECT_ID"
    log_success "Created Pub/Sub trigger"
else
    log_info "Pub/Sub trigger already exists"
fi

# Trigger for monitoring alerts
log_info "Creating monitoring alerts trigger..."
if ! gcloud eventarc triggers describe nervous-system-monitoring --location="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    run_cmd gcloud eventarc triggers create nervous-system-monitoring \
        --location="$REGION" \
        --destination-run-service="$SERVICE_NAME" \
        --destination-run-region="$REGION" \
        --destination-run-path="/v1/nexus/v1/eventarc/monitoring" \
        --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
        --transport-topic="projects/$PROJECT_ID/topics/nervous-system-alerts" \
        --service-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$PROJECT_ID"
    log_success "Created monitoring trigger"
else
    log_info "Monitoring trigger already exists"
fi

# Step 7: Verify deployment
log_info "Step 7: Verifying deployment..."
echo ""
echo "📋 Eventarc Triggers:"
gcloud eventarc triggers list --location="$REGION" --project="$PROJECT_ID" \
    --filter="name~nervous-system" \
    --format="table(name,eventFilters,destination.cloudRun.service)"

echo ""
echo "📋 Pub/Sub Topics:"
gcloud pubsub topics list --project="$PROJECT_ID" \
    --filter="name~nervous-system" \
    --format="table(name)"

# Step 8: Test endpoint
log_info "Step 8: Testing health endpoint..."
HEALTH_URL="${SERVICE_URL}/v1/nexus/v1/eventarc/health"
if curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" | grep -q "200"; then
    log_success "Health endpoint responding"
else
    log_warn "Health endpoint not responding (service may need restart)"
fi

echo ""
echo "🧬 =================================================================="
echo "   DEPLOYMENT COMPLETE!"
echo ""
echo "   Endpoints:"
echo "   - Webhook:    ${SERVICE_URL}/v1/nexus/v1/eventarc/webhook"
echo "   - Logging:    ${SERVICE_URL}/v1/nexus/v1/eventarc/logging"
echo "   - Monitoring: ${SERVICE_URL}/v1/nexus/v1/eventarc/monitoring"
echo "   - Pub/Sub:    ${SERVICE_URL}/v1/nexus/v1/eventarc/pubsub"
echo "   - Stats:      ${SERVICE_URL}/v1/nexus/v1/eventarc/stats"
echo "   - Health:     ${SERVICE_URL}/v1/nexus/v1/eventarc/health"
echo ""
echo "   Test command:"
echo "   curl -X POST ${SERVICE_URL}/v1/nexus/v1/eventarc/test-stimulus"
echo ""
echo "🧬 =================================================================="
