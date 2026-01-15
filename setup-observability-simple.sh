#!/bin/bash
# Simplified Observability Setup - Using Available APIs Only

set -e

PROJECT_ID="${PROJECT_ID:-vertice-ai}"

echo "📊 OBSERVABILIDADE SIMPLIFICADA - APIs Disponíveis"
echo "=================================================="

echo "🔍 Verificando APIs disponíveis..."
gcloud services list --project=$PROJECT_ID --filter="name:(monitoring OR logging)" --format="value(name)"

echo ""
echo "📈 Configurando dashboards básicos..."

# Create a simple monitoring dashboard
cat <<EOF > dashboard.json
{
  "displayName": "Vertice SaaS Basic Monitoring",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Cloud Run Request Count",
        "xyChart": {
          "dataSets": [
            {
              "plotType": "LINE",
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\"",
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

gcloud monitoring dashboards create --config-from-file=dashboard.json --project=$PROJECT_ID 2>/dev/null || echo "Dashboard creation skipped - API may not be available"

echo ""
echo "✅ Observabilidade básica configurada!"
echo ""
echo "📊 Dashboards disponíveis em: https://console.cloud.google.com/monitoring/dashboards"