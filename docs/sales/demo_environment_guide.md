# Vertice-Code Enterprise Demo Environment
## Production-Like Demo Setup Guide

**Version 1.0 | May 2026 | Vertice-Code Enterprise Sales**

---

## Executive Summary

This guide provides step-by-step instructions for setting up a production-like demo environment that showcases Vertice-Code's enterprise capabilities. The demo environment simulates a real enterprise development workflow, complete with integrations, security controls, and performance monitoring.

**Demo Goals:**
- Demonstrate full enterprise feature set
- Showcase integration capabilities
- Validate performance and scalability
- Provide hands-on evaluation experience

---

## 🏗️ Demo Architecture

### Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DEMO ENVIRONMENT                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐   │
│  │   Vertice-Code  │ │  Demo Database  │ │  Monitoring │   │
│  │   Application   │ │   (Firestore)   │ │   (Grafana) │   │
│  └─────────────────┘ └─────────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
               │                       │                       │
┌──────────────┼───────────────────────┼───────────────────────┼──────────────┐
│  ┌─────────┐ │ ┌─────────┐ ┌─────────┐ │ ┌─────────┐ ┌─────────┐ │ ┌─────────┐ │
│  │ GitHub  │ │ │ GitLab  │ │ Jenkins │ │ │ Service │ │  Slack  │ │ │  Jira   │ │
│  │ Actions │ │ │  CI/CD  │ │         │ │ │  Now    │ │         │ │ │         │ │
│  └─────────┘ │ └─────────┘ └─────────┘ │ └─────────┘ └─────────┘ │ └─────────┘ │
└──────────────┼───────────────────────┼───────────────────────┼──────────────┼──────────────┘
               │                       │                       │
        ┌──────┴──────┐       ┌────────┴────────┐       ┌──────┴──────┐
        │  Demo Code  │       │   Test Data     │       │   Analytics │
        │ Repository  │       │   Generation    │       │   Dashboard │
        └─────────────┘       └─────────────────┘       └─────────────┘
```

### Component Specifications

#### Vertice-Code Application
- **Version**: Enterprise v1.0
- **Deployment**: Google Cloud Run (multi-region)
- **Database**: Firestore (production configuration)
- **CDN**: Firebase Hosting with global distribution
- **Security**: All enterprise security features enabled

#### Demo Data
- **Code Repository**: 50+ sample projects across industries
- **User Accounts**: 100 pre-configured demo users
- **Historical Data**: 6 months of simulated usage data
- **Integration Events**: Pre-generated webhook payloads

#### Monitoring & Analytics
- **Real-time Metrics**: Live usage dashboards
- **Performance Monitoring**: Response times and error rates
- **Integration Health**: Connection status for all integrations
- **Security Events**: Simulated security monitoring

---

## 🚀 Quick Start Setup

### Prerequisites

#### System Requirements
- **OS**: Linux/macOS/Windows (WSL2 recommended)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 20GB free space
- **Network**: Stable internet connection (100Mbps+)

#### Software Dependencies
```bash
# Docker and Docker Compose
docker --version  # 24.0+
docker-compose --version  # 2.0+

# Git
git --version  # 2.30+

# Python (for local development)
python --version  # 3.11+

# Node.js (for frontend components)
node --version  # 18.0+
npm --version  # 9.0+
```

### One-Click Demo Setup

#### Step 1: Clone Repository
```bash
git clone https://github.com/JuanCS-Dev/vertice-code.git
cd vertice-code
git checkout enterprise-demo
```

#### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.demo .env

# Edit configuration (optional - defaults work for demo)
nano .env
```

#### Step 3: Launch Demo Environment
```bash
# Start all services
docker-compose -f docker-compose.demo.yml up -d

# Wait for services to be healthy (2-3 minutes)
docker-compose -f docker-compose.demo.yml ps

# Verify demo is running
curl http://localhost:8080/health
```

#### Step 4: Access Demo
```bash
# Web Interface
open http://localhost:8080

# API Documentation
open http://localhost:8080/docs

# Monitoring Dashboard
open http://localhost:8081

# Grafana Metrics
open http://localhost:3000
```

---

## 🔧 Detailed Configuration

### Environment Variables

```bash
# Demo Environment Configuration
VERTICE_ENV=demo
VERTICE_DEMO_MODE=true
VERTICE_DEMO_DATA_LOAD=true

# Application Settings
VERTICE_PORT=8080
VERTICE_HOST=0.0.0.0
VERTICE_DEBUG=true

# Database Configuration
FIRESTORE_PROJECT_ID=vertice-demo
FIRESTORE_EMULATOR_HOST=localhost:8081

# Authentication (Demo Mode)
VERTICE_AUTH_BYPASS=true
VERTICE_DEMO_USERS=admin@example.com,user1@example.com,user2@example.com

# Integrations (Mock Mode)
VERTICE_GITHUB_MOCK=true
VERTICE_SLACK_MOCK=true
VERTICE_JIRA_MOCK=true

# Analytics & Monitoring
VERTICE_ANALYTICS_ENABLED=true
VERTICE_METRICS_ENABLED=true
VERTICE_LOG_LEVEL=INFO
```

### Custom Demo Scenarios

#### Scenario 1: Enterprise Onboarding
```bash
# Load enterprise onboarding demo data
docker-compose -f docker-compose.demo.yml exec vertice python scripts/load_demo_data.py --scenario enterprise_onboarding

# Simulate user activities
docker-compose -f docker-compose.demo.yml exec vertice python scripts/simulate_activity.py --users 50 --duration 300
```

#### Scenario 2: Compliance Demonstration
```bash
# Load compliance-focused demo data
docker-compose -f docker-compose.demo.yml exec vertice python scripts/load_demo_data.py --scenario compliance_demo

# Generate audit logs
docker-compose -f docker-compose.demo.yml exec vertice python scripts/generate_audit_logs.py --days 30
```

#### Scenario 3: Integration Showcase
```bash
# Load integration demo data
docker-compose -f docker-compose.demo.yml exec vertice python scripts/load_demo_data.py --scenario integrations

# Simulate webhook events
docker-compose -f docker-compose.demo.yml exec vertice python scripts/simulate_webhooks.py --integrations github,slack,jira --events 100
```

---

## 🎯 Demo Scenarios & Scripts

### Enterprise Onboarding Demo

#### Objective
Demonstrate the complete white-glove onboarding process for enterprise customers.

#### Key Features Showcased
- Automated environment provisioning
- Custom integration setup
- SLA configuration
- Success metrics dashboard
- Multi-user collaboration

#### Demo Script
```bash
# 1. Start with tenant creation
curl -X POST http://localhost:8080/api/v1/pilots \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "demo-enterprise",
    "company_name": "Demo Corporation",
    "pricing_tier": "enterprise",
    "expected_users": 500,
    "custom_integrations": ["github", "slack", "jira"]
  }'

# 2. Monitor onboarding progress
watch -n 5 'curl http://localhost:8080/api/v1/pilots/demo-pilot/progress'

# 3. Show completed integrations
curl http://localhost:8080/api/v1/tenants/demo-enterprise/integrations

# 4. Demonstrate analytics dashboard
open http://localhost:8080/demo/analytics
```

### Compliance & Security Demo

#### Objective
Showcase enterprise-grade security and compliance capabilities.

#### Key Features Showcased
- SOC 2 Type II controls
- GDPR compliance features
- Audit logging and reporting
- Security monitoring
- Data encryption

#### Demo Script
```bash
# 1. Show compliance dashboard
open http://localhost:8080/demo/compliance

# 2. Demonstrate audit logging
curl http://localhost:8080/api/v1/tenants/demo-enterprise/audit-logs

# 3. Show security events
curl http://localhost:8080/api/v1/security/events

# 4. Demonstrate data encryption
curl http://localhost:8080/api/v1/demo/encryption-demo
```

### Performance & Scalability Demo

#### Objective
Demonstrate enterprise-scale performance and reliability.

#### Key Features Showcased
- Multi-LLM orchestration
- Real-time streaming AI
- Auto-scaling capabilities
- Performance monitoring
- Error handling

#### Demo Script
```bash
# 1. Start performance test
docker-compose -f docker-compose.demo.yml exec vertice python scripts/performance_test.py --users 100 --duration 300

# 2. Monitor real-time metrics
open http://localhost:3000/d/performance-dashboard

# 3. Show AI orchestration in action
curl -X POST http://localhost:8080/api/v1/code/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a REST API for user management",
    "context": {"language": "python", "framework": "fastapi"},
    "orchestrate": true
  }'

# 4. Demonstrate error recovery
curl http://localhost:8080/api/v1/demo/error-recovery
```

---

## 🔌 Integration Demonstrations

### GitHub Integration Demo

#### Setup
```bash
# Enable GitHub mock integration
echo "VERTICE_GITHUB_MOCK=true" >> .env

# Restart services
docker-compose -f docker-compose.demo.yml restart
```

#### Demo Flow
```bash
# 1. Create demo repository
curl -X POST http://localhost:8080/api/v1/demo/github/repo \
  -H "Content-Type: application/json" \
  -d '{"name": "demo-app", "description": "Demo application"}'

# 2. Simulate pull request
curl -X POST http://localhost:8080/api/v1/demo/github/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": "pull_request.opened",
    "repository": "demo/demo-app",
    "pull_request": {"number": 1, "title": "Add user authentication"}
  }'

# 3. Show AI code review
curl http://localhost:8080/api/v1/demo/github/review/1
```

### Slack Integration Demo

#### Setup
```bash
# Configure Slack mock
echo "VERTICE_SLACK_MOCK=true" >> .env
echo "VERTICE_SLACK_WEBHOOK_URL=http://localhost:8080/demo/slack/webhook" >> .env
```

#### Demo Flow
```bash
# 1. Send deployment notification
curl -X POST http://localhost:8080/api/v1/demo/slack/notify \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#engineering",
    "message": "🚀 Production deployment completed successfully",
    "attachments": [
      {"color": "good", "text": "Version: v1.2.3\nEnvironment: Production\nDuration: 5m 23s"}
    ]
  }'

# 2. Show interactive features
open http://localhost:8080/demo/slack/interactive
```

### Jira Integration Demo

#### Setup
```bash
# Enable Jira mock integration
echo "VERTICE_JIRA_MOCK=true" >> .env
echo "VERTICE_JIRA_BASE_URL=http://localhost:8080/demo/jira" >> .env
```

#### Demo Flow
```bash
# 1. Create issue from code analysis
curl -X POST http://localhost:8080/api/v1/demo/jira/issue \
  -H "Content-Type: application/json" \
  -d '{
    "project": "DEMO",
    "type": "Bug",
    "summary": "Security vulnerability in authentication module",
    "description": "High-severity SQL injection vulnerability detected",
    "labels": ["security", "critical"]
  }'

# 2. Update issue status
curl -X PUT http://localhost:8080/api/v1/demo/jira/issue/DEMO-123 \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress", "assignee": "security-team"}'

# 3. Show issue dashboard
open http://localhost:8080/demo/jira/dashboard
```

---

## 📊 Monitoring & Analytics

### Grafana Dashboards

#### Access Dashboards
```bash
# Default credentials: admin/admin
open http://localhost:3000

# Demo dashboards:
# - Performance Overview
# - Integration Health
# - Security Events
# - User Activity
# - AI Model Performance
```

#### Key Metrics to Monitor
- **Response Times**: API endpoint performance
- **Error Rates**: System reliability metrics
- **Integration Status**: Connection health for all integrations
- **User Activity**: Active users and session data
- **AI Performance**: Model response times and accuracy

### Application Metrics

#### Real-time Monitoring
```bash
# System health
curl http://localhost:8080/health

# Metrics endpoint
curl http://localhost:8080/metrics

# Integration status
curl http://localhost:8080/api/v1/integrations/status
```

#### Performance Testing
```bash
# Load testing script
docker-compose -f docker-compose.demo.yml exec vertice python scripts/load_test.py --requests 1000 --concurrency 10

# AI performance test
docker-compose -f docker-compose.demo.yml exec vertice python scripts/ai_performance_test.py --models 5 --iterations 100
```

---

## 🛠️ Troubleshooting

### Common Issues

#### Demo Won't Start
```bash
# Check Docker status
docker ps

# View logs
docker-compose -f docker-compose.demo.yml logs vertice

# Restart services
docker-compose -f docker-compose.demo.yml down
docker-compose -f docker-compose.demo.yml up -d
```

#### Slow Performance
```bash
# Check resource usage
docker stats

# Increase Docker resources
# Docker Desktop: Settings > Resources > Advanced

# Clear demo data
docker-compose -f docker-compose.demo.yml exec vertice python scripts/clear_demo_data.py
```

#### Integration Failures
```bash
# Check integration status
curl http://localhost:8080/api/v1/integrations/status

# Reset integrations
docker-compose -f docker-compose.demo.yml exec vertice python scripts/reset_integrations.py

# Check mock services
docker-compose -f docker-compose.demo.yml ps
```

#### Data Loading Issues
```bash
# Reload demo data
docker-compose -f docker-compose.demo.yml exec vertice python scripts/load_demo_data.py --force

# Check data integrity
docker-compose -f docker-compose.demo.yml exec vertice python scripts/validate_demo_data.py
```

---

## 📚 Demo Resources

### Pre-built Demo Scripts
- `scripts/demo_enterprise_onboarding.py` - Complete onboarding walkthrough
- `scripts/demo_compliance_showcase.py` - Security and compliance features
- `scripts/demo_integration_tour.py` - All integration demonstrations
- `scripts/demo_performance_test.py` - Scalability and performance showcase

### Sample Data Sets
- `data/demo_projects/` - Sample code repositories
- `data/demo_users/` - Pre-configured user accounts
- `data/demo_integrations/` - Integration configuration examples
- `data/demo_analytics/` - Historical usage and performance data

### Presentation Materials
- `docs/demo_scripts/` - Guided demo scripts for sales team
- `docs/demo_slides/` - PowerPoint presentation templates
- `docs/demo_videos/` - Recorded demo walkthroughs
- `docs/demo_faq/` - Frequently asked questions

---

## 🎯 Best Practices

### Demo Preparation
1. **System Check**: Verify all services are running
2. **Data Freshness**: Reload demo data before each session
3. **Network Stability**: Ensure reliable internet connection
4. **Browser Compatibility**: Test on target customer's browser

### During Demo
1. **Pace Control**: Allow time for questions and exploration
2. **Feature Focus**: Highlight 3-5 key features per demo
3. **Real Scenarios**: Use customer's industry-specific examples
4. **Technical Depth**: Balance business and technical content

### Follow-up
1. **Demo Recording**: Provide access to recorded session
2. **Custom Demo**: Offer personalized demo based on requirements
3. **Technical Deep-dive**: Schedule technical architecture review
4. **Pilot Planning**: Discuss proof-of-concept implementation

---

## 📞 Support & Resources

### Demo Environment Support
- **Demo Portal**: https://demo.vertice.ai
- **Documentation**: https://docs.vertice.ai/demo
- **Support Ticket**: demo-support@vertice.ai
- **Slack Channel**: #demo-support

### Sales Enablement
- **Demo Training**: Weekly demo certification sessions
- **Best Practices**: Monthly demo improvement workshops
- **Competitive Scenarios**: Mock competitive demo battles
- **Customer Feedback**: Demo effectiveness surveys

---

*This demo environment provides a comprehensive showcase of Vertice-Code's enterprise capabilities. Regular updates ensure the latest features and integrations are always demonstrated.*

**Last updated: May 2026**