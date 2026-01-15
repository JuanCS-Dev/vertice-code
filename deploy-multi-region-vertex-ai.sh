#!/bin/bash
# Multi-Region Vertex AI Auto-Scaling Deployment
# Deploys HPA and Deployments for Vertex AI across US, EU, Asia regions

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"
REGIONS=("us-central1" "europe-west1" "asia-southeast1")

echo "🚀 Deploying multi-region Vertex AI auto-scaling infrastructure..."

# ============================================
# Function to deploy region-specific resources
# ============================================
deploy_region() {
    local region=$1
    local region_short=$2

    echo "📍 Deploying Vertex AI for $region..."

    # Apply deployment
    kubectl apply -f "k8s/deployment-vertex-ai-${region_short}.yaml"

    # Apply HPA
    kubectl apply -f "k8s/hpa-vertex-ai-${region_short}.yaml"

    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/vertice-vertex-ai-${region_short} -n vertice

    echo "✅ Vertex AI deployed in $region"
}

# ============================================
# Create namespace if it doesn't exist
# ============================================
kubectl create namespace vertice --dry-run=client -o yaml | kubectl apply -f -

# ============================================
# Deploy Service Account
# ============================================
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vertice-vertex-ai-sa
  namespace: vertice
  annotations:
    iam.gke.io/gcp-service-account: vertice-vertex-ai@${PROJECT_ID}.iam.gserviceaccount.com
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: vertice-vertex-ai-sa-binding
subjects:
- kind: ServiceAccount
  name: vertice-vertex-ai-sa
  namespace: vertice
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF

# ============================================
# Deploy to each region
# ============================================
deploy_region "us-central1" "us"
deploy_region "europe-west1" "eu"
deploy_region "asia-southeast1" "asia"

# ============================================
# Create Global Service for load balancing
# ============================================
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: vertice-vertex-ai-global
  namespace: vertice
  annotations:
    cloud.google.com/neg: '{"ingress": true}'
    networking.gke.io/load-balancer-type: "GlobalExternal"
spec:
  type: LoadBalancer
  selector:
    app: vertice-vertex-ai
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8080
    protocol: TCP
    name: https
EOF

# ============================================
# Verify deployment
# ============================================
echo ""
echo "🔍 Verifying deployment status..."
kubectl get deployments -n vertice -l app=vertice-vertex-ai
kubectl get hpa -n vertice -l app=vertice-vertex-ai

echo ""
echo "🎉 Multi-region Vertex AI auto-scaling deployment complete!"
echo ""
echo "📊 Monitoring:"
echo "  • HPA status: kubectl get hpa -n vertice"
echo "  • Pod scaling: kubectl get pods -n vertice -l app=vertice-vertex-ai"
echo "  • Metrics: kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1"
echo ""
echo "🔧 Scaling behavior:"
echo "  • CPU > 70%: Scale up pods"
echo "  • Memory > 80%: Scale up pods"
echo "  • AI requests > 100/sec: Scale up pods"
echo "  • Scale up: Fast (100% pods/min)"
echo "  • Scale down: Conservative (20% pods/min, 5min stabilization)"