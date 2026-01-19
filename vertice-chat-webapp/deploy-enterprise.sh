#!/bin/bash

# Enterprise Cloud Run Deployment Script
# Multi-region deployment with auto-scaling

set -e

PROJECT_ID="vertice-ai"
IMAGE_NAME="gcr.io/${PROJECT_ID}/backend:v1-enterprise"
SERVICE_NAME="vertice-backend"

echo "🚀 Starting enterprise Cloud Run deployment..."

# Deploy to US Central (Primary)
echo "📍 Deploying to US Central (Primary Region)..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=5 \
  --max-instances=1000 \
  --concurrency=80 \
  --timeout=300 \
  --set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest \
  --set-secrets=VERTEX_AI_KEY=vertex-ai-key:latest \
  --set-env-vars=NODE_ENV=production \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --set-env-vars=PRIMARY_REGION=true

# Deploy to EU West (DR Region)
echo "📍 Deploying to EU West (DR Region)..."
gcloud run deploy ${SERVICE_NAME}-eu \
  --image=${IMAGE_NAME} \
  --platform=managed \
  --region=europe-west1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=2 \
  --max-instances=500 \
  --concurrency=80 \
  --timeout=300 \
  --set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest \
  --set-secrets=VERTEX_AI_KEY=vertex-ai-key:latest \
  --set-env-vars=NODE_ENV=production \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --set-env-vars=DR_REGION=true

# Configure Load Balancing (Serverless NEGs)
echo "⚖️ Configuring load balancing..."

# Create serverless NEGs for each region
gcloud compute network-endpoint-groups create ${SERVICE_NAME}-us-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=${SERVICE_NAME}

gcloud compute network-endpoint-groups create ${SERVICE_NAME}-eu-neg \
  --region=europe-west1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=${SERVICE_NAME}-eu

# Create backend services
gcloud compute backend-services create ${SERVICE_NAME}-backend \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --protocol=HTTPS \
  --port-name=https \
  --timeout=30s

# Add backends
gcloud compute backend-services add-backend ${SERVICE_NAME}-backend \
  --network-endpoint-group=${SERVICE_NAME}-us-neg \
  --network-endpoint-group-region=us-central1 \
  --balancing-mode=UTILIZATION \
  --capacity-scaler=1.0

gcloud compute backend-services add-backend ${SERVICE_NAME}-backend \
  --network-endpoint-group=${SERVICE_NAME}-eu-neg \
  --network-endpoint-group-region=europe-west1 \
  --balancing-mode=UTILIZATION \
  --capacity-scaler=1.0

# Create URL map
gcloud compute url-maps create ${SERVICE_NAME}-url-map \
  --default-service=${SERVICE_NAME}-backend

# Create SSL certificate
gcloud compute ssl-certificates create ${SERVICE_NAME}-cert \
  --domains=app.vertice-maximus.com

# Create target HTTPS proxy
gcloud compute target-https-proxies create ${SERVICE_NAME}-proxy \
  --ssl-certificates=${SERVICE_NAME}-cert \
  --url-map=${SERVICE_NAME}-url-map

# Create global forwarding rule
gcloud compute forwarding-rules create ${SERVICE_NAME}-forwarding-rule \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --target-https-proxy=${SERVICE_NAME}-proxy \
  --ports=443 \
  --global \
  --address=app.vertice-maximus.com

echo "✅ Enterprise deployment completed!"
echo "🌐 Primary: https://app.vertice-maximus.com (US)"
echo "🌍 DR: https://eu.app.vertice-maximus.com (EU)"

# Health checks
echo "🔍 Running health checks..."
sleep 30

US_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://${SERVICE_NAME}-abc123-uc.a.run.app/health)
EU_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://${SERVICE_NAME}-eu-abc123-ew.a.run.app/health)

if [ "$US_HEALTH" = "200" ] && [ "$EU_HEALTH" = "200" ]; then
  echo "✅ All services healthy!"
else
  echo "❌ Health check failed - US: $US_HEALTH, EU: $EU_HEALTH"
  exit 1
fi

echo "🎉 Enterprise infrastructure deployment successful!"
