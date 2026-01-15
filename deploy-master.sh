#!/bin/bash
# Master Deployment Script for Vertice Enterprise SaaS
# Executes all deployment steps in correct order

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-vertice-ai}"
REGION="${REGION:-us-central1}"

echo -e "${BLUE}🚀 VERTICE ENTERPRISE SAAS - DEPLOYMENT MASTER SCRIPT${NC}"
echo -e "${BLUE}====================================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi

    # Check if firebase is installed
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI not found. Please install Firebase CLI."
        exit 1
    fi

    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Run 'gcloud auth login'"
        exit 1
    fi

    # Set project
    gcloud config set project $PROJECT_ID

    # Check if project exists
    if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
        print_error "Project $PROJECT_ID does not exist or you don't have access."
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to enable required APIs
enable_apis() {
    print_status "Enabling required GCP APIs..."

    APIs=(
        "cloudbuild.googleapis.com"
        "container.googleapis.com"
        "run.googleapis.com"
        "firebase.googleapis.com"
        "aiplatform.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
        "trace.googleapis.com"
        "pubsub.googleapis.com"
        "secretmanager.googleapis.com"
        "compute.googleapis.com"
        "artifactregistry.googleapis.com"
        "iam.googleapis.com"
    )

    for api in "${APIs[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable $api --project=$PROJECT_ID
    done

    print_success "All APIs enabled"
}

# Function to create GKE cluster
create_gke_cluster() {
    print_status "Creating GKE Autopilot cluster..."

    # Check if cluster already exists
    if gcloud container clusters list --project=$PROJECT_ID --region=$REGION --filter="name:vertice-cluster" --format="value(name)" | grep -q .; then
        print_warning "GKE cluster 'vertice-cluster' already exists"
        return
    fi

    gcloud container clusters create-auto vertice-cluster \
        --region=$REGION \
        --project=$PROJECT_ID \
        --enable-autopilot \
        --enable-private-nodes \
        --enable-private-endpoint \
        --master-ipv4-cidr=172.16.0.0/28

    print_success "GKE cluster created"
}

# Function to setup Firebase
setup_firebase() {
    print_status "Setting up Firebase..."

    firebase use $PROJECT_ID

    # Initialize Firebase if not already done
    if [ ! -f ".firebaserc" ]; then
        firebase init hosting --project=$PROJECT_ID
    fi

    print_success "Firebase configured"
}

# Function to run deployment scripts
run_deployment_scripts() {
    print_status "Running deployment scripts in sequence..."

    scripts=(
        "./setup-multi-region-firebase.sh"
        "./deploy-multi-region-vertex-ai.sh"
        "./setup-observability.sh"
        "./setup-zero-trust-security.sh"
        "./optimize-ai-performance.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            print_status "Executing $script..."
            chmod +x "$script"
            bash "$script"
            print_success "$script completed"
        else
            print_error "Script $script not found"
            exit 1
        fi
    done
}

# Function to run validation tests
run_validation_tests() {
    print_status "Running validation tests..."

    # Check if services are running
    print_status "Checking deployed services..."

    # Check Cloud Run services
    if gcloud run services list --project=$PROJECT_ID --region=$REGION --format="value(name)" | grep -q "vertice"; then
        print_success "Cloud Run services deployed"
    else
        print_warning "No Cloud Run services found"
    fi

    # Check GKE workloads
    if kubectl get pods -n vertice --no-headers 2>/dev/null | grep -q .; then
        print_success "Kubernetes workloads running"
    else
        print_warning "No Kubernetes workloads found"
    fi

    print_success "Validation completed"
}

# Main execution
main() {
    echo "Starting Vertice Enterprise SaaS deployment..."
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo ""

    check_prerequisites
    enable_apis
    create_gke_cluster
    setup_firebase
    run_deployment_scripts
    run_validation_tests

    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
    echo ""
    echo -e "${BLUE}📋 NEXT STEPS:${NC}"
    echo "1. Access your application at the provided URLs"
    echo "2. Monitor services in GCP Console"
    echo "3. Configure custom domains if needed"
    echo "4. Set up monitoring alerts"
    echo ""
    echo -e "${BLUE}🚀 YOUR ENTERPRISE SAAS IS LIVE!${NC}"
}

# Run main function
main "$@"