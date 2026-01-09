import express from 'express';
import { logAudit } from './security';
import { Firestore } from '@google-cloud/firestore';

const firestore = new Firestore({ projectId: 'vertice-ai' });

// Tenant configuration
export interface Tenant {
  id: string;
  name: string;
  plan: 'starter' | 'professional' | 'enterprise';
  status: 'active' | 'suspended' | 'provisioning';
  adminEmail: string;
  createdAt: Date;
  settings: TenantSettings;
  quotas: TenantQuotas;
}

export interface TenantSettings {
  maxUsers: number;
  maxStorage: string;
  features: string[];
  customDomain?: string;
  branding?: {
    logo?: string;
    colors?: Record<string, string>;
  };
}

export interface TenantQuotas {
  users: { current: number; limit: number };
  storage: { current: number; limit: number };
  apiCalls: { current: number; limit: number };
  aiTokens: { current: number; limit: number };
}

// Tenant quotas by plan
const PLAN_QUOTAS = {
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
};

// Extend Express Request type
declare global {
  namespace Express {
    interface Request {
      tenant?: Tenant;
    }
  }
}

// Tenant middleware - extracts tenant from subdomain or header
export function tenantMiddleware(req: express.Request, res: express.Response, next: express.NextFunction) {
  try {
    let tenantId: string | null = null;

    // Extract tenant from subdomain (e.g., company.vertice.ai)
    const host = req.headers.host;
    if (host) {
      const subdomain = host.split('.')[0];
      if (subdomain !== 'www' && subdomain !== 'app' && subdomain !== host.split(':')[0]) {
        tenantId = subdomain;
      }
    }

    // Fallback: Extract from header (for API calls)
    if (!tenantId) {
      tenantId = req.headers['x-tenant-id'] as string;
    }

    // Fallback: Extract from JWT token (enterprise SSO)
    if (!tenantId && req.headers.authorization) {
      // In production: decode JWT and extract tenant claim
      tenantId = 'default'; // Placeholder
    }

    if (!tenantId) {
      logAudit('tenant_not_found', 'unknown', { host, headers: req.headers });
      return res.status(400).json({
        error: 'Tenant not specified',
        message: 'Please provide tenant ID via subdomain or X-Tenant-ID header'
      });
    }

    // Validate tenant exists and is active
    getTenant(tenantId).then(tenant => {
      if (!tenant) {
        logAudit('tenant_not_found', 'unknown', { tenantId });
        return res.status(404).json({ error: 'Tenant not found' });
      }

      if (tenant.status !== 'active') {
        logAudit('tenant_inactive', 'unknown', { tenantId, status: tenant.status });
        return res.status(403).json({ error: 'Tenant is not active' });
      }

      // Attach tenant to request
      req.tenant = tenant;
      logAudit('tenant_context_set', tenant.adminEmail, { tenantId });
      next();
    }).catch(error => {
      logAudit('tenant_lookup_error', 'unknown', { tenantId, error: (error as Error).message });
      res.status(500).json({ error: 'Tenant validation failed' });
    });

  } catch (error) {
    logAudit('tenant_middleware_error', 'unknown', { error: (error as Error).message });
    res.status(500).json({ error: 'Tenant middleware error' });
  }
}

// Tenant management functions
export async function getTenant(tenantId: string): Promise<Tenant | null> {
  try {
    const doc = await firestore.collection('tenants').doc(tenantId).get();
    if (!doc.exists) return null;

    const data = doc.data();
    return {
      id: doc.id,
      ...data
    } as Tenant;
  } catch (error) {
    console.error('Error getting tenant:', error);
    return null;
  }
}

export async function createTenant(tenantData: Pick<Tenant, 'name' | 'plan' | 'adminEmail' | 'status'>): Promise<Tenant> {
  try {
    const tenantId = generateTenantId();
    const tenant: Tenant = {
      ...tenantData,
      id: tenantId,
      createdAt: new Date(),
      quotas: {
        users: { current: 0, limit: PLAN_QUOTAS[tenantData.plan].users },
        storage: { current: 0, limit: parseStorageLimit(PLAN_QUOTAS[tenantData.plan].storage) },
        apiCalls: { current: 0, limit: PLAN_QUOTAS[tenantData.plan].apiCalls },
        aiTokens: { current: 0, limit: PLAN_QUOTAS[tenantData.plan].aiTokens }
      },
      settings: {
        maxUsers: PLAN_QUOTAS[tenantData.plan].users,
        maxStorage: PLAN_QUOTAS[tenantData.plan].storage,
        features: getPlanFeatures(tenantData.plan)
      }
    };

    await firestore.collection('tenants').doc(tenantId).set(tenant);
    logAudit('tenant_created', tenantData.adminEmail, { tenantId, plan: tenantData.plan });

    return tenant;
  } catch (error) {
    logAudit('tenant_creation_error', tenantData.adminEmail, { error: (error as Error).message });
    throw new Error('Failed to create tenant');
  }
}

export async function updateTenantQuotas(tenantId: string, resource: keyof TenantQuotas, amount: number): Promise<void> {
  try {
    const tenantRef = firestore.collection('tenants').doc(tenantId);
    await firestore.runTransaction(async (transaction) => {
      const doc = await transaction.get(tenantRef);
      if (!doc.exists) throw new Error('Tenant not found');

      const tenant = doc.data() as Tenant;
      tenant.quotas[resource].current += amount;

      transaction.update(tenantRef, { quotas: tenant.quotas });
    });

    logAudit('tenant_quota_updated', 'system', { tenantId, resource, amount });
  } catch (error) {
    logAudit('tenant_quota_update_error', 'system', { tenantId, resource, error: (error as Error).message });
    throw error;
  }
}

export async function checkTenantQuota(tenantId: string, resource: keyof TenantQuotas, requested: number): Promise<boolean> {
  try {
    const tenant = await getTenant(tenantId);
    if (!tenant) return false;

    const quota = tenant.quotas[resource];
    return (quota.current + requested) <= quota.limit;
  } catch (error) {
    console.error('Error checking tenant quota:', error);
    return false;
  }
}

// Helper functions
function generateTenantId(): string {
  return `tenant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function parseStorageLimit(storage: string): number {
  const match = storage.match(/(\d+)(GB|MB|KB)/);
  if (!match) return 0;

  const [, size, unit] = match;
  const multipliers = { KB: 1024, MB: 1024 * 1024, GB: 1024 * 1024 * 1024 };
  return parseInt(size) * multipliers[unit as keyof typeof multipliers];
}

function getPlanFeatures(plan: string): string[] {
  const features = {
    starter: ['basic-ai', 'chat-history', 'export'],
    professional: ['starter', 'advanced-ai', 'team-collaboration', 'api-access'],
    enterprise: ['professional', 'white-label', 'sso', 'audit-logs', 'custom-integration']
  };

  return features[plan as keyof typeof features] || [];
}

// Tenant provisioning (async background task)
export async function provisionTenantResources(tenantId: string): Promise<void> {
  try {
    // Create tenant-specific Firestore collections
    await firestore.collection('tenants').doc(tenantId).collection('settings').doc('default').set({
      theme: 'default',
      language: 'en',
      timezone: 'UTC'
    });

    // Set up security rules for tenant isolation
    // Note: This would be done via Firebase Admin SDK or console

    logAudit('tenant_resources_provisioned', 'system', { tenantId });
  } catch (error) {
    logAudit('tenant_provisioning_error', 'system', { tenantId, error: (error as Error).message });
    throw error;
  }
}