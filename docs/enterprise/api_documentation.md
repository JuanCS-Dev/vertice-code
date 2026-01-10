# Vertice-Code Enterprise API Documentation
## OpenAPI 3.0 Specification

This document provides comprehensive API documentation for enterprise integrations with Vertice-Code.

### Base URL
```
https://api.vertice.ai/v1
```

### Authentication
All API requests require authentication using Bearer tokens:

```
Authorization: Bearer <your-api-key>
```

Enterprise customers receive dedicated API keys with appropriate permissions.

### Rate Limits
- **Enterprise Tier**: 10,000 requests per hour
- **Enterprise Plus**: 50,000 requests per hour
- **Enterprise Elite**: Unlimited (with fair usage policy)

---

## Core Endpoints

### Tenants

#### Create Tenant
```http
POST /tenants
```

**Request Body:**
```json
{
  "company_name": "Acme Corporation",
  "pricing_tier": "enterprise",
  "expected_users": 500,
  "custom_integrations": ["slack", "github"],
  "technical_contact": {
    "email": "admin@acme.com",
    "name": "Jane Smith"
  },
  "business_contact": {
    "email": "ceo@acme.com",
    "name": "John Doe"
  }
}
```

**Response (201):**
```json
{
  "tenant_id": "tenant_abc123",
  "status": "provisioning",
  "estimated_completion": "2026-05-15T10:00:00Z",
  "success_manager": "enterprise-success@vertice.ai"
}
```

#### Get Tenant Status
```http
GET /tenants/{tenant_id}
```

**Response (200):**
```json
{
  "tenant_id": "tenant_abc123",
  "status": "active",
  "created_at": "2026-05-01T09:00:00Z",
  "pricing_tier": "enterprise",
  "active_users": 245,
  "integrations": ["slack", "github", "jira"]
}
```

### Pilot Onboarding

#### Initiate Pilot Setup
```http
POST /pilots
```

**Request Body:**
```json
{
  "tenant_id": "tenant_abc123",
  "pilot_config": {
    "duration_days": 90,
    "expected_users": 100,
    "custom_integrations": ["salesforce", "servicenow"],
    "sla_requirements": {
      "response_time_hours": 4,
      "uptime_percentage": 99.9
    }
  }
}
```

**Response (202):**
```json
{
  "pilot_id": "pilot_xyz789",
  "status": "initializing",
  "estimated_completion": "2026-05-01T12:00:00Z",
  "onboarding_steps": [
    {
      "name": "environment_provisioning",
      "description": "Provision isolated tenant environment",
      "status": "pending"
    }
  ]
}
```

#### Get Pilot Progress
```http
GET /pilots/{pilot_id}/progress
```

**Response (200):**
```json
{
  "pilot_id": "pilot_xyz789",
  "overall_progress": 85.7,
  "status": "active",
  "completed_steps": 5,
  "total_steps": 6,
  "current_step": "metrics_dashboard",
  "estimated_completion": "2026-05-01T11:30:00Z",
  "success_manager": "sarah@vertice.ai"
}
```

### Analytics & Metrics

#### Get Tenant Analytics
```http
GET /tenants/{tenant_id}/analytics
```

**Query Parameters:**
- `start_date` (ISO 8601)
- `end_date` (ISO 8601)
- `metrics` (comma-separated list)

**Response (200):**
```json
{
  "tenant_id": "tenant_abc123",
  "period": {
    "start": "2026-04-01T00:00:00Z",
    "end": "2026-05-01T00:00:00Z"
  },
  "metrics": {
    "active_users": 245,
    "total_sessions": 15420,
    "ai_tokens_used": 2500000,
    "average_response_time_ms": 850,
    "error_rate_percentage": 0.15,
    "uptime_percentage": 99.95
  },
  "trends": {
    "user_growth": 15.2,
    "usage_increase": 22.8
  }
}
```

#### Get Success Metrics
```http
GET /tenants/{tenant_id}/success-metrics
```

**Response (200):**
```json
{
  "tenant_id": "tenant_abc123",
  "satisfaction_score": 87.5,
  "adoption_rate": 78.3,
  "churn_risk_score": 12.4,
  "expansion_opportunities": 3,
  "recommendations": [
    "Consider additional training for advanced features",
    "Monitor integration performance with Salesforce"
  ]
}
```

### Integrations

#### List Available Integrations
```http
GET /integrations
```

**Response (200):**
```json
{
  "integrations": [
    {
      "name": "slack",
      "display_name": "Slack",
      "category": "communication",
      "status": "available",
      "setup_required": true
    },
    {
      "name": "github",
      "display_name": "GitHub",
      "category": "development",
      "status": "available",
      "setup_required": true
    },
    {
      "name": "salesforce",
      "display_name": "Salesforce",
      "category": "crm",
      "status": "enterprise_only",
      "setup_required": true
    }
  ]
}
```

#### Configure Integration
```http
POST /tenants/{tenant_id}/integrations/{integration_name}
```

**Request Body:**
```json
{
  "config": {
    "webhook_url": "https://hooks.slack.com/services/...",
    "channels": ["#general", "#engineering"],
    "events": ["code_review_completed", "deployment_success"]
  }
}
```

**Response (201):**
```json
{
  "integration_id": "int_slack_001",
  "status": "configuring",
  "estimated_activation": "2026-05-01T10:15:00Z"
}
```

### Billing & Usage

#### Get Usage Report
```http
GET /tenants/{tenant_id}/billing/usage
```

**Query Parameters:**
- `period` (monthly|quarterly|yearly)
- `start_date` (ISO 8601)

**Response (200):**
```json
{
  "tenant_id": "tenant_abc123",
  "period": "2026-04",
  "usage": {
    "ai_tokens": 2500000,
    "active_users": 245,
    "storage_gb": 500,
    "api_calls": 45000
  },
  "costs": {
    "base_tier": 1999.00,
    "overage_tokens": 125.00,
    "overage_users": 0.00,
    "total": 2124.00
  },
  "next_billing_date": "2026-06-01"
}
```

---

## Webhooks

### Pilot Status Updates
```http
POST {configured_webhook_url}
```

**Payload:**
```json
{
  "event_type": "pilot.status_update",
  "pilot_id": "pilot_xyz789",
  "timestamp": "2026-05-01T10:30:00Z",
  "data": {
    "status": "completed",
    "completion_percentage": 100.0,
    "success_manager": "sarah@vertice.ai",
    "next_steps": [
      "Schedule kickoff call",
      "Begin user training"
    ]
  }
}
```

### Integration Events
```http
POST {configured_webhook_url}
```

**Payload:**
```json
{
  "event_type": "integration.notification",
  "integration": "github",
  "timestamp": "2026-05-01T11:00:00Z",
  "data": {
    "event": "pull_request_merged",
    "repository": "acme/main-app",
    "pr_number": 123,
    "author": "developer@acme.com",
    "ai_analysis": {
      "code_quality_score": 8.7,
      "security_issues": 0,
      "performance_impact": "neutral"
    }
  }
}
```

---

## Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid tenant configuration",
    "details": {
      "field": "expected_users",
      "issue": "Must be positive integer"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2026-05-01T10:00:00Z"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request data
- `AUTHENTICATION_ERROR`: Invalid or missing credentials
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SERVICE_UNAVAILABLE`: Temporary service issues

---

## SDKs & Libraries

### Python SDK
```bash
pip install vertice-enterprise
```

```python
from vertice_enterprise import VerticeClient

client = VerticeClient(api_key="your-api-key")

# Create tenant
tenant = await client.tenants.create({
    "company_name": "Acme Corp",
    "pricing_tier": "enterprise"
})

# Monitor pilot progress
progress = await client.pilots.get_progress("pilot_xyz789")
print(f"Pilot {progress.overall_progress}% complete")
```

### Node.js SDK
```bash
npm install @vertice/enterprise
```

```javascript
const { VerticeClient } = require('@vertice/enterprise');

const client = new VerticeClient({ apiKey: 'your-api-key' });

// Get analytics
const analytics = await client.tenants.getAnalytics('tenant_abc123');
console.log(`Active users: ${analytics.metrics.active_users}`);
```

---

*Last updated: May 2026 | Version: 1.0.0*