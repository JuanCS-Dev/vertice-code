import express from 'express';
import { logAudit, requireAuth, validateInput } from '../security';
import { ssoService } from '../sso';
import { rbacService, requirePermission, PERMISSIONS, ROLES } from '../rbac';

const router = express.Router();

// SSO Endpoints (Enterprise Feature)
router.post('/sso/azure/setup', requireAuth, async (req, res) => {
  try {
    const { clientId, clientSecret, tenantId } = req.body;

    const ssoId = await ssoService.createAzureSSO('tenant_id', {
      clientId,
      clientSecret,
      tenantId
    });

    res.json({ ssoId, provider: 'azure', status: 'configured' });
  } catch (error) {
    res.status(500).json({ error: 'Azure SSO setup failed' });
  }
});

router.post('/sso/okta/setup', requireAuth, async (req, res) => {
  try {
    const { clientId, clientSecret, domain } = req.body;

    const ssoId = await ssoService.createOktaSSO('tenant_id', {
      clientId,
      clientSecret,
      domain
    });

    res.json({ ssoId, provider: 'okta', status: 'configured' });
  } catch (error) {
    res.status(500).json({ error: 'Okta SSO setup failed' });
  }
});

router.post('/sso/saml/setup', requireAuth, async (req, res) => {
  try {
    const samlConfig = req.body;

    const ssoId = await ssoService.createSAMLSSO('tenant_id', samlConfig);
    res.json({ ssoId, provider: 'saml', status: 'configured' });
  } catch (error) {
    res.status(500).json({ error: 'SAML SSO setup failed' });
  }
});

router.get('/sso/:ssoId/authorize', async (req, res) => {
  try {
    const { ssoId } = req.params;
    const { redirect_uri } = req.query;

    const authUrl = await ssoService.getAuthorizationUrl(ssoId, redirect_uri as string);
    res.redirect(authUrl);
  } catch (error) {
    res.status(500).json({ error: 'SSO authorization failed' });
  }
});

router.get('/sso/:ssoId/callback', async (req, res) => {
  try {
    const { ssoId } = req.params;
    const { code, state } = req.query;

    const userInfo = await ssoService.processCallback(ssoId, code as string, state as string);

    // Here you would typically create/update user session
    // For now, return user info
    res.json({
      user: userInfo,
      status: 'authenticated',
      redirect: state || '/dashboard'
    });
  } catch (error) {
    res.status(500).json({ error: 'SSO callback failed' });
  }
});

router.get('/sso/configs', requireAuth, async (req, res) => {
  try {
    const configs = await ssoService.getTenantSSOConfigs('tenant_id');
    res.json({ ssoConfigs: configs });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get SSO configs' });
  }
});

// RBAC Endpoints (Enterprise Feature)
router.post('/rbac/roles/assign', requireAuth, requirePermission(PERMISSIONS.USER_MANAGE_ROLES), async (req, res) => {
  try {
    const { userId, roleName } = req.body;

    // Check if assigner can assign this role
    const canAssign = await rbacService.canAssignRole('assigner_id', 'tenant_id', roleName);
    if (!canAssign) {
      return res.status(403).json({ error: 'Insufficient permissions to assign this role' });
    }

    await rbacService.assignRole(userId, 'tenant_id', roleName, 'assigner_id');
    res.json({ message: 'Role assigned successfully' });
  } catch (error) {
    logAudit('role_assignment_failed', 'user_id', { error: (error as Error).message });
    res.status(500).json({ error: 'Role assignment failed' });
  }
});

router.delete('/rbac/roles/:userId/:roleName', requireAuth, requirePermission(PERMISSIONS.USER_MANAGE_ROLES), async (req, res) => {
  try {
    const { userId, roleName } = req.params;

    await rbacService.removeRole(userId, 'tenant_id', roleName, 'remover_id');
    res.json({ message: 'Role removed successfully' });
  } catch (error) {
    logAudit('role_removal_failed', 'user_id', { error: (error as Error).message });
    res.status(500).json({ error: 'Role removal failed' });
  }
});

router.get('/rbac/roles/:userId', requireAuth, async (req, res) => {
  try {
    const { userId } = req.params;

    const roles = await rbacService.getUserRoles(userId, 'tenant_id');
    res.json({ roles });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get user roles' });
  }
});

router.get('/rbac/permissions/check', requireAuth, async (req, res) => {
  try {
    const { permission } = req.query;

    const hasPermission = await rbacService.hasPermission('user_id', 'tenant_id', permission as string);
    res.json({ hasPermission });
  } catch (error) {
    res.status(500).json({ error: 'Permission check failed' });
  }
});

router.get('/rbac/roles', requireAuth, async (req, res) => {
  try {
    const availableRoles = rbacService.getAvailableRoles();
    res.json({ roles: availableRoles });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get available roles' });
  }
});

router.post('/rbac/roles/custom', requireAuth, requirePermission(PERMISSIONS.USER_MANAGE_ROLES), async (req, res) => {
  try {
    const { name, description, permissions } = req.body;

    const roleId = await rbacService.createCustomRole('tenant_id', {
      name,
      description,
      permissions,
      createdBy: 'creator_id'
    });

    res.json({ roleId, status: 'created' });
  } catch (error) {
    logAudit('custom_role_creation_failed', 'user_id', { error: (error as Error).message });
    res.status(500).json({ error: 'Custom role creation failed' });
  }
});

router.get('/rbac/users/:roleName', requireAuth, async (req, res) => {
  try {
    const { roleName } = req.params;

    const users = await rbacService.getUsersByRole('tenant_id', roleName);
    res.json({ users });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get users by role' });
  }
});

export default router;