# Multi-Tenancy Architecture - Vertice-Chat SaaS

## Overview

Enterprise-grade multi-tenancy implementation with complete data isolation, resource quotas, and tenant management.

## Architecture

### 1. Data Isolation Strategy

#### Collection-Level Isolation
```
Firestore Structure:
/tenants/{tenantId}/users/{userId}
/tenants/{tenantId}/chats/{chatId}
/tenants/{tenantId}/settings/{settingId}
/tenants/{tenantId}/billing/{billingId}
```

#### Benefits:
- Complete data isolation between tenants
- Easy tenant migration/scaling
- Simplified compliance (GDPR per tenant)
- Cost allocation per tenant

### 2. Resource Quotas & Limits

#### Per-Tenant Limits:
- **Users**: 1-1000 users per tenant
- **Storage**: 1GB-100GB per tenant
- **API Calls**: 10K-1M requests/month
- **AI Tokens**: 100K-10M tokens/month

#### Quota Enforcement:
```typescript
const tenantQuotas = {
  starter: {
    users: 10,
    storage: '1GB',
    apiCalls: 10000,
    aiTokens: 100000
  },
  professional: {
    users: 100,
    storage: '10GB',
    apiCalls: 100000,
    aiTokens: 1000000
  },
  enterprise: {
    users: 1000,
    storage: '100GB',
    apiCalls: 1000000,
    aiTokens: 10000000
  }
}
```

### 3. Tenant Provisioning

#### Automated Setup:
1. Create tenant record in `/tenants/{tenantId}`
2. Set up Firestore security rules
3. Configure VPC Service Controls
4. Initialize default settings
5. Send welcome email

### 4. Security Model

#### VPC Service Controls:
```json
{
  "policymember": {
    "resource": "projects/vertice-ai",
    "policy": {
      "bindings": [
        {
          "role": "roles/storage.objectViewer",
          "members": ["serviceAccount:tenant-{tenantId}@vertice-ai.iam.gserviceaccount.com"]
        }
      ]
    }
  }
}
```

#### Firestore Security Rules:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Tenant isolation
    match /tenants/{tenantId}/{document=**} {
      allow read, write: if request.auth != null &&
        getTenantRole(request.auth.uid, tenantId) in ['owner', 'admin', 'user'];
    }

    // Global collections (read-only for tenants)
    match /global/{document=**} {
      allow read: if request.auth != null;
    }
  }
}
```

## Implementation Phases

### Phase 1: Core Multi-Tenancy (Current)
- [x] Tenant data isolation
- [x] Basic tenant management
- [x] Resource quota system
- [ ] Tenant provisioning API
- [ ] Tenant migration tools

### Phase 2: Advanced Features (Next)
- [ ] VPC Service Controls per tenant
- [ ] Custom domains per tenant
- [ ] White-label branding
- [ ] Tenant-specific AI models
- [ ] Advanced analytics per tenant

### Phase 3: Enterprise Scale (Future)
- [ ] Multi-region tenant replication
- [ ] Tenant backup/restore
- [ ] Cross-tenant collaboration
- [ ] Tenant marketplace

## Technical Implementation

### Tenant Context Middleware
```typescript
// middleware/tenant-context.ts
export function tenantMiddleware(req: Request, res: Response, next: NextFunction) {
  // Extract tenant from subdomain or header
  const tenantId = extractTenantId(req);

  if (!tenantId) {
    return res.status(400).json({ error: 'Tenant not specified' });
  }

  // Validate tenant exists and is active
  const tenant = await getTenant(tenantId);
  if (!tenant || !tenant.active) {
    return res.status(404).json({ error: 'Tenant not found' });
  }

  // Attach tenant context to request
  req.tenant = tenant;
  next();
}
```

### Quota Enforcement
```typescript
// services/quota-service.ts
export class QuotaService {
  async checkQuota(tenantId: string, resource: string, amount: number): Promise<boolean> {
    const quota = await this.getTenantQuota(tenantId, resource);
    const current = await this.getCurrentUsage(tenantId, resource);

    return (current + amount) <= quota.limit;
  }

  async enforceQuota(tenantId: string, resource: string, amount: number): Promise<void> {
    if (!await this.checkQuota(tenantId, resource, amount)) {
      throw new Error(`Quota exceeded for ${resource}`);
    }

    await this.incrementUsage(tenantId, resource, amount);
  }
}
```

### Tenant Management API
```typescript
// routes/tenant-management.ts
app.post('/api/tenants', requireAuth, async (req, res) => {
  const { name, plan, adminEmail } = req.body;

  // Create tenant
  const tenantId = generateTenantId();
  const tenant = await createTenant({
    id: tenantId,
    name,
    plan,
    adminEmail,
    status: 'provisioning'
  });

  // Provision resources asynchronously
  provisionTenantResources(tenantId);

  res.json({ tenantId, status: 'provisioning' });
});

app.get('/api/tenants/:tenantId', requireAuth, async (req, res) => {
  const { tenantId } = req.params;

  // Verify user has access to tenant
  if (!await userHasTenantAccess(req.user.id, tenantId)) {
    return res.status(403).json({ error: 'Access denied' });
  }

  const tenant = await getTenant(tenantId);
  res.json(tenant);
});
```

## Migration Strategy

### From Single-Tenant to Multi-Tenant

1. **Data Migration**: Move existing data to tenant-specific collections
2. **User Migration**: Assign all users to default tenant
3. **Code Updates**: Add tenant context to all operations
4. **Testing**: Comprehensive testing of tenant isolation

### Zero-Downtime Migration
- Use Firestore exports/imports
- Gradual rollout with feature flags
- Rollback plan prepared
- Monitoring throughout migration

## Monitoring & Compliance

### Tenant-Specific Metrics
- Usage per tenant
- Performance per tenant
- Security events per tenant
- Compliance status per tenant

### Audit & Compliance
- Complete audit trail per tenant
- GDPR compliance per tenant
- SOC 2 controls per tenant
- Regular compliance assessments

## Scaling Considerations

### Horizontal Scaling
- Multiple Cloud Run instances per tenant
- Firestore collection sharding
- CDN distribution per tenant

### Cost Optimization
- Resource pooling where safe
- Pay-per-tenant pricing
- Usage-based scaling
- Automated resource cleanup

---

*Status: Core multi-tenancy implemented - 60% complete*
*Next: VPC Service Controls and advanced tenant features*