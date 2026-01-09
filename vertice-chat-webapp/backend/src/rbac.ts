import { Firestore } from '@google-cloud/firestore';
import { logAudit } from './security';

const firestore = new Firestore({ projectId: 'vertice-ai' });

// RBAC Enterprise Implementation

// Permission definitions
export const PERMISSIONS = {
  // User Management
  USER_READ: 'user:read',
  USER_CREATE: 'user:create',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',
  USER_INVITE: 'user:invite',
  USER_MANAGE_ROLES: 'user:manage_roles',

  // Tenant Management
  TENANT_READ: 'tenant:read',
  TENANT_UPDATE: 'tenant:update',
  TENANT_DELETE: 'tenant:delete',
  TENANT_BILLING: 'tenant:billing',
  TENANT_SETTINGS: 'tenant:settings',

  // AI/Chat Features
  AI_CHAT: 'ai:chat',
  AI_CODE_GENERATE: 'ai:code_generate',
  AI_CODE_REVIEW: 'ai:code_review',
  AI_CUSTOM_MODELS: 'ai:custom_models',
  AI_USAGE_ANALYTICS: 'ai:usage_analytics',

  // Content Management
  CONTENT_READ: 'content:read',
  CONTENT_CREATE: 'content:create',
  CONTENT_UPDATE: 'content:update',
  CONTENT_DELETE: 'content:delete',
  CONTENT_PUBLISH: 'content:publish',

  // Analytics & Reporting
  ANALYTICS_READ: 'analytics:read',
  ANALYTICS_EXPORT: 'analytics:export',
  REPORTS_CREATE: 'reports:create',
  DASHBOARD_CUSTOMIZE: 'dashboard:customize',

  // Security & Compliance
  SECURITY_AUDIT_READ: 'security:audit_read',
  SECURITY_INCIDENT_REPORT: 'security:incident_report',
  COMPLIANCE_VIEW: 'compliance:view',
  COMPLIANCE_AUDIT: 'compliance:audit',

  // Integration Management
  INTEGRATION_READ: 'integration:read',
  INTEGRATION_CREATE: 'integration:create',
  INTEGRATION_UPDATE: 'integration:update',
  INTEGRATION_DELETE: 'integration:delete',

  // API Access
  API_ACCESS: 'api:access',
  API_RATE_LIMIT_BYPASS: 'api:rate_limit_bypass',
  WEBHOOK_MANAGE: 'webhook:manage',

  // Administrative
  ADMIN_SYSTEM_CONFIG: 'admin:system_config',
  ADMIN_BACKUP: 'admin:backup',
  ADMIN_MAINTENANCE: 'admin:maintenance',
  ADMIN_USER_IMPERSONATE: 'admin:user_impersonate'
} as const;

// Role definitions with permissions
export const ROLES = {
  // Basic User Roles
  VIEWER: {
    name: 'Viewer',
    description: 'Read-only access to basic features',
    permissions: [
      'ai:chat',
      'content:read',
      'analytics:read'
    ] as any,
    level: 1
  },

  CONTRIBUTOR: {
    name: 'Contributor',
    description: 'Can create and edit content',
    permissions: [
      'ai:chat',
      'ai:code_generate',
      'content:read',
      'content:create',
      'content:update',
      'analytics:read'
    ] as any,
    level: 2
  },

  DEVELOPER: {
    name: 'Developer',
    description: 'Full access to development features',
    permissions: [
      'ai:chat',
      'ai:code_generate',
      'ai:code_review',
      'content:read',
      'content:create',
      'content:update',
      'content:delete',
      'integration:read',
      'api:access',
      'analytics:read',
      'analytics:export'
    ] as any,
    level: 3
  },

  TEAM_LEAD: {
    name: 'Team Lead',
    description: 'Leadership access with team management',
    permissions: [
      'user:read',
      'user:invite',
      'content:publish',
      'reports:create',
      'dashboard:customize',
      'integration:read',
      'integration:create',
      'integration:update',
      'webhook:manage',
      'ai:usage_analytics'
    ] as any,
    level: 4
  },

  // Administrative Roles
  COMPLIANCE_OFFICER: {
    name: 'Compliance Officer',
    description: 'Security and compliance oversight',
    permissions: [
      'security:audit_read',
      'security:incident_report',
      'compliance:view',
      'compliance:audit',
      'user:read',
      'analytics:read',
      'analytics:export'
    ] as any,
    level: 5
  },

  BILLING_ADMIN: {
    name: 'Billing Admin',
    description: 'Billing and subscription management',
    permissions: [
      'tenant:read',
      'tenant:billing',
      'analytics:read',
      'analytics:export',
      'reports:create'
    ] as any,
    level: 5
  },

  IT_ADMIN: {
    name: 'IT Admin',
    description: 'Technical administration',
    permissions: [
      'user:read',
      'user:create',
      'user:update',
      'user:delete',
      'user:invite',
      'integration:read',
      'integration:create',
      'integration:update',
      'integration:delete',
      'api:access',
      'webhook:manage',
      'security:audit_read'
    ] as any,
    level: 6
  },

  // Executive Roles
  DEPARTMENT_HEAD: {
    name: 'Department Head',
    description: 'Department leadership with budget oversight',
    permissions: [
      'user:manage_roles',
      'tenant:read',
      'tenant:update',
      'tenant:billing',
      'ai:custom_models',
      'security:audit_read',
      'compliance:view'
    ] as any,
    level: 7
  },

  CFO: {
    name: 'Chief Financial Officer',
    description: 'Financial oversight and billing',
    permissions: [
      'tenant:read',
      'tenant:billing',
      'tenant:settings',
      'analytics:read',
      'analytics:export',
      'reports:create',
      'user:read'
    ] as any,
    level: 8
  },

  CTO: {
    name: 'Chief Technology Officer',
    description: 'Technical leadership and system access',
    permissions: [
      'admin:system_config',
      'admin:backup',
      'admin:maintenance',
      'security:incident_report',
      'compliance:audit'
    ] as any,
    level: 9
  },

  // Custom Roles for Flexibility
  CUSTOM_ANALYST: {
    name: 'Custom Analyst',
    description: 'Advanced analytics and reporting',
    permissions: [
      'analytics:read',
      'analytics:export',
      'reports:create',
      'dashboard:customize',
      'ai:usage_analytics'
    ] as any,
    level: 3
  },

  AUDITOR: {
    name: 'Auditor',
    description: 'Read-only access for auditing purposes',
    permissions: [
      'security:audit_read',
      'compliance:view',
      'analytics:read',
      'user:read',
      'tenant:read'
    ] as any,
    level: 2
  },

  INTEGRATION_SPECIALIST: {
    name: 'Integration Specialist',
    description: 'API and integration management',
    permissions: [
      'integration:read',
      'integration:create',
      'integration:update',
      'integration:delete',
      'api:access',
      'webhook:manage',
      'content:read'
    ] as any,
    level: 4
  }
} as const;

// RBAC Service Implementation
class RBACService {
  // Check if user has permission
  async hasPermission(userId: string, tenantId: string, permission: string): Promise<boolean> {
    try {
      // Get user roles for tenant
      const userRoles = await this.getUserRoles(userId, tenantId);

      // Check if any role has the permission
      for (const roleName of userRoles) {
        const role = ROLES[roleName as keyof typeof ROLES];
        if (role && role.permissions.includes(permission)) {
          return true;
        }
      }

      return false;
    } catch (error) {
      logAudit('rbac_permission_check_error', userId, { tenantId, permission, error: (error as Error).message });
      return false;
    }
  }

  // Check if user has any of the permissions
  async hasAnyPermission(userId: string, tenantId: string, permissions: string[]): Promise<boolean> {
    for (const permission of permissions) {
      if (await this.hasPermission(userId, tenantId, permission)) {
        return true;
      }
    }
    return false;
  }

  // Check if user has all permissions
  async hasAllPermissions(userId: string, tenantId: string, permissions: string[]): Promise<boolean> {
    for (const permission of permissions) {
      if (!await this.hasPermission(userId, tenantId, permission)) {
        return false;
      }
    }
    return true;
  }

  // Assign role to user
  async assignRole(userId: string, tenantId: string, roleName: string, assignedBy: string): Promise<void> {
    try {
      if (!ROLES[roleName as keyof typeof ROLES]) {
        throw new Error(`Invalid role: ${roleName}`);
      }

      const roleAssignment = {
        userId,
        tenantId,
        roleName,
        assignedBy,
        assignedAt: new Date(),
        active: true
      };

      await firestore.collection('user_roles')
        .doc(`${tenantId}_${userId}_${roleName}`)
        .set(roleAssignment);

      logAudit('role_assigned', assignedBy, { userId, tenantId, roleName });

    } catch (error) {
      logAudit('role_assignment_error', assignedBy, { userId, tenantId, roleName, error: (error as Error).message });
      throw error;
    }
  }

  // Remove role from user
  async removeRole(userId: string, tenantId: string, roleName: string, removedBy: string): Promise<void> {
    try {
      await firestore.collection('user_roles')
        .doc(`${tenantId}_${userId}_${roleName}`)
        .update({
          active: false,
          removedBy,
          removedAt: new Date()
        });

      logAudit('role_removed', removedBy, { userId, tenantId, roleName });

    } catch (error) {
      logAudit('role_removal_error', removedBy, { userId, tenantId, roleName, error: (error as Error).message });
      throw error;
    }
  }

  // Get user roles for tenant
  async getUserRoles(userId: string, tenantId: string): Promise<string[]> {
    try {
      const rolesSnapshot = await firestore.collection('user_roles')
        .where('userId', '==', userId)
        .where('tenantId', '==', tenantId)
        .where('active', '==', true)
        .get();

      return rolesSnapshot.docs.map(doc => doc.data().roleName);
    } catch (error) {
      logAudit('get_user_roles_error', userId, { tenantId, error: (error as Error).message });
      return [];
    }
  }

  // Get all users with specific role in tenant
  async getUsersByRole(tenantId: string, roleName: string): Promise<string[]> {
    try {
      const usersSnapshot = await firestore.collection('user_roles')
        .where('tenantId', '==', tenantId)
        .where('roleName', '==', roleName)
        .where('active', '==', true)
        .get();

      return usersSnapshot.docs.map(doc => doc.data().userId);
    } catch (error) {
      logAudit('get_users_by_role_error', 'system', { tenantId, roleName, error: (error as Error).message });
      return [];
    }
  }

  // Create custom role
  async createCustomRole(tenantId: string, roleDefinition: {
    name: string;
    description: string;
    permissions: string[];
    createdBy: string;
  }): Promise<string> {
    try {
      const roleId = `custom_${tenantId}_${Date.now()}`;

      const customRole = {
        id: roleId,
        tenantId,
        name: roleDefinition.name,
        description: roleDefinition.description,
        permissions: roleDefinition.permissions,
        isCustom: true,
        createdBy: roleDefinition.createdBy,
        createdAt: new Date(),
        level: 3 // Default level for custom roles
      };

      await firestore.collection('custom_roles').doc(roleId).set(customRole);

      logAudit('custom_role_created', roleDefinition.createdBy, { roleId, tenantId, roleName: roleDefinition.name });

      return roleId;
    } catch (error) {
      logAudit('custom_role_creation_error', roleDefinition.createdBy, { tenantId, error: (error as Error).message });
      throw error;
    }
  }

  // Get role hierarchy level
  getRoleLevel(roleName: string): number {
    const role = ROLES[roleName as keyof typeof ROLES];
    return role ? role.level : 1;
  }

  // Check if user can assign role (role hierarchy)
  async canAssignRole(assignerId: string, tenantId: string, targetRole: string): Promise<boolean> {
    try {
      const assignerRoles = await this.getUserRoles(assignerId, tenantId);
      const maxAssignerLevel = Math.max(...assignerRoles.map(role => this.getRoleLevel(role)));
      const targetLevel = this.getRoleLevel(targetRole);

      return maxAssignerLevel > targetLevel;
    } catch (error) {
      return false;
    }
  }

  // Get role permissions
  getRolePermissions(roleName: string): string[] {
    const role = ROLES[roleName as keyof typeof ROLES];
    return role ? role.permissions : [];
  }

  // Validate permission exists
  isValidPermission(permission: string): boolean {
    return Object.values(PERMISSIONS).includes(permission as any);
  }

  // List all available roles
  getAvailableRoles(): any[] {
    return Object.entries(ROLES).map(([key, role]) => ({
      name: key,
      description: role.description,
      level: role.level,
      permissions: [...role.permissions]
    }));
  }
}

// RBAC Middleware
export function requirePermission(permission: string) {
  return async (req: any, res: any, next: any) => {
    try {
      const userId = req.user?.id || 'anonymous';
      const tenantId = req.tenant?.id || 'default';

      const rbacService = new RBACService();
      const hasPermission = await rbacService.hasPermission(userId, tenantId, permission);

      if (!hasPermission) {
        logAudit('permission_denied', userId, { tenantId, permission, path: req.path });
        return res.status(403).json({
          error: 'Insufficient permissions',
          required: permission
        });
      }

      logAudit('permission_granted', userId, { tenantId, permission, path: req.path });
      next();
    } catch (error) {
      logAudit('permission_check_error', 'system', { permission, error: (error as Error).message });
      res.status(500).json({ error: 'Permission check failed' });
    }
  };
}

// Initialize RBAC service
export const rbacService = new RBACService();

export { RBACService };