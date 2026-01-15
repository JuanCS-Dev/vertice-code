#!/bin/bash
# Distributed Tracing and APM Integration Setup
# Deploys OpenTelemetry, Jaeger, and Prometheus for comprehensive observability

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"

echo "🚀 Setting up distributed tracing and APM integration..."

# ============================================
# Create GCP Monitoring & Logging resources
# ============================================
echo "📊 Creating GCP monitoring resources..."

# Enable required APIs
gcloud services enable monitoring.googleapis.com \
    logging.googleapis.com \
    trace.googleapis.com \
    --project=$PROJECT_ID

# Create custom metrics
gcloud monitoring metrics-descriptors create custom.googleapis.com/opentelemetry/ai_requests_per_second \
    --description="AI inference requests per second" \
    --metric-kind=GAUGE \
    --value-type=DOUBLE \
    --unit="1/s" \
    --project=$PROJECT_ID

gcloud monitoring metrics-descriptors create custom.googleapis.com/opentelemetry/ai_inference_latency \
    --description="AI inference latency in milliseconds" \
    --metric-kind=GAUGE \
    --value-type=DOUBLE \
    --unit="ms" \
    --project=$PROJECT_ID

# Create log sink for OpenTelemetry
gcloud logging sinks create vertice-otel-logs \
    pubsub.googleapis.com/projects/$PROJECT_ID/topics/vertice-otel-logs \
    --log-filter='resource.type="k8s_container" AND resource.labels.cluster_name="vertice-cluster"' \
    --project=$PROJECT_ID

# Create Pub/Sub topic and subscription
gcloud pubsub topics create vertice-otel-logs --project=$PROJECT_ID
gcloud pubsub subscriptions create vertice-logs-sub \
    --topic=vertice-otel-logs \
    --project=$PROJECT_ID

# ============================================
# Deploy Kubernetes monitoring stack
# ============================================
echo "🔧 Deploying Kubernetes monitoring stack..."

# Apply OpenTelemetry Collector
kubectl apply -f k8s/otel-collector-config.yaml
kubectl apply -f k8s/otel-collector-deployment.yaml

# Apply Jaeger for distributed tracing
kubectl apply -f k8s/jaeger-deployment.yaml

# Apply Prometheus for metrics and alerting
kubectl apply -f k8s/prometheus-deployment.yaml

# ============================================
# Create Service Accounts and RBAC
# ============================================
echo "🔐 Setting up service accounts and permissions..."

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vertice-observability-sa
  namespace: vertice
  annotations:
    iam.gke.io/gcp-service-account: vertice-observability@${PROJECT_ID}.iam.gserviceaccount.com
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vertice-prometheus-sa
  namespace: vertice
  annotations:
    iam.gke.io/gcp-service-account: vertice-prometheus@${PROJECT_ID}.iam.gserviceaccount.com
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vertice-observability-role
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "services", "endpoints", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: vertice-observability-binding
subjects:
- kind: ServiceAccount
  name: vertice-observability-sa
  namespace: vertice
roleRef:
  kind: ClusterRole
  name: vertice-observability-role
  apiGroup: rbac.authorization.k8s.io
EOF

# ============================================
# Create AlertManager configuration
# ============================================
echo "📢 Setting up alerting..."

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: vertice
data:
  config.yml: |
    global:
      smtp_smarthost: 'smtp.gmail.com:587'
      smtp_from: 'alerts@vertice.ai'
      smtp_auth_username: 'alerts@vertice.ai'
      smtp_auth_password: 'your-smtp-password'

    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'email-notifications'
      routes:
      - match:
          severity: critical
        receiver: 'email-notifications'

    receivers:
    - name: 'email-notifications'
      email_configs:
      - to: 'devops@vertice.ai'
        send_resolved: true
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: vertice
  labels:
    app: alertmanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:latest
        ports:
        - containerPort: 9093
          name: http
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
        resources:
          requests:
            cpu: "50m"
            memory: "128Mi"
          limits:
            cpu: "100m"
            memory: "256Mi"
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: vertice
  labels:
    app: alertmanager
spec:
  type: LoadBalancer
  ports:
  - name: http
    port: 9093
    targetPort: 9093
  selector:
    app: alertmanager
EOF

# ============================================
# Wait for deployments
# ============================================
echo "⏳ Waiting for deployments to be ready..."

kubectl wait --for=condition=available --timeout=300s deployment/opentelemetry-collector -n vertice
kubectl wait --for=condition=available --timeout=300s deployment/jaeger -n vertice
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-server -n vertice
kubectl wait --for=condition=available --timeout=300s deployment/alertmanager -n vertice

# ============================================
# Create dashboards
# ============================================
echo "📊 Setting up monitoring dashboards..."

# Create custom dashboard in Cloud Monitoring
gcloud monitoring dashboards create --config-from-file=dashboard-config.json --project=$PROJECT_ID <<EOF
{
  "displayName": "Vertice AI Observability Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "AI Inference Latency",
        "xyChart": {
          "dataSets": [
            {
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/opentelemetry/ai_inference_latency\" resource.type=\"k8s_container\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }
          ]
        }
      },
      {
        "title": "AI Requests per Second",
        "xyChart": {
          "dataSets": [
            {
              "plotType": "LINE",
              "targetAxis": "Y1",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/opentelemetry/ai_requests_per_second\" resource.type=\"k8s_container\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}
EOF

# ============================================
# Verify setup
# ============================================
echo ""
echo "🔍 Verifying observability setup..."
kubectl get deployments -n vertice -l component=observability
kubectl get deployments -n vertice -l component=monitoring
kubectl get deployments -n vertice -l component=tracing

echo ""
echo "🎉 Distributed tracing and APM integration complete!"
echo ""
echo "📋 Access URLs:"
echo "  • Prometheus: http://prometheus-server.vertice.svc.cluster.local:9090"
echo "  • Jaeger UI: http://jaeger-ui.vertice.svc.cluster.local:16686"
echo "  • AlertManager: http://alertmanager.vertice.svc.cluster.local:9093"
echo "  • OpenTelemetry Collector: http://opentelemetry-collector.vertice.svc.cluster.local:8888"
echo ""
echo "📊 Cloud Monitoring:"
echo "  • Dashboard: https://console.cloud.google.com/monitoring/dashboards"
echo "  • Custom Metrics: custom.googleapis.com/opentelemetry/*"
echo "  • Traces: https://console.cloud.google.com/traces"
echo ""
echo "🔧 Integration Notes:"
echo "  • Applications should export OTLP traces to: otel-collector:4317 (gRPC) or 4318 (HTTP)"
echo "  • Metrics are auto-scraped via Prometheus annotations"
echo "  • Alerts are sent to devops@vertice.ai (configure SMTP credentials)"
echo "  • Use Jaeger for local development debugging"