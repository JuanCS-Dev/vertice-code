import express from 'express';
import { Firestore } from '@google-cloud/firestore';
import { logAudit, requireAuth } from './security';

const firestore = new Firestore({ projectId: 'vertice-ai' });

// SSO Configuration Interface
interface SSOConfig {
  provider: 'azure' | 'okta' | 'google' | 'saml';
  clientId: string;
  clientSecret: string;
  tenantId?: string; // For Azure
  domain?: string; // For Okta
  metadataUrl?: string; // For SAML
  enabled: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// SAML 2.0 Service Provider Configuration
interface SAMLConfig {
  entityId: string;
  assertionConsumerServiceUrl: string;
  singleLogoutServiceUrl: string;
  nameIdFormat: string;
  signingCertificate: string;
  encryptionCertificate?: string;
}

// SSO Provider Implementations
class SSOService {
  private ssoConfigs: Map<string, SSOConfig> = new Map();

  // Initialize SSO providers
  async initializeProviders(): Promise<void> {
    try {
      // Load SSO configurations from Firestore
      const configs = await firestore.collection('sso_configs').get();

      configs.docs.forEach(doc => {
        const config = doc.data() as SSOConfig;
        this.ssoConfigs.set(doc.id, config);
      });

      logAudit('sso_providers_initialized', 'system', { providerCount: configs.size });
    } catch (error) {
      logAudit('sso_initialization_error', 'system', { error: (error as Error).message });
      throw error;
    }
  }

  // Azure AD SSO Implementation
  async createAzureSSO(tenantId: string, config: Partial<SSOConfig>): Promise<string> {
    const ssoId = `azure_${tenantId}_${Date.now()}`;

    const azureConfig: SSOConfig = {
      provider: 'azure',
      clientId: config.clientId || '',
      clientSecret: config.clientSecret || '',
      tenantId: config.tenantId || tenantId,
      enabled: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await firestore.collection('sso_configs').doc(ssoId).set(azureConfig);
    this.ssoConfigs.set(ssoId, azureConfig);

    logAudit('azure_sso_created', 'admin', { ssoId, tenantId });
    return ssoId;
  }

  // Okta SSO Implementation
  async createOktaSSO(tenantId: string, config: Partial<SSOConfig>): Promise<string> {
    const ssoId = `okta_${tenantId}_${Date.now()}`;

    const oktaConfig: SSOConfig = {
      provider: 'okta',
      clientId: config.clientId || '',
      clientSecret: config.clientSecret || '',
      domain: config.domain || '',
      enabled: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await firestore.collection('sso_configs').doc(ssoId).set(oktaConfig);
    this.ssoConfigs.set(ssoId, oktaConfig);

    logAudit('okta_sso_created', 'admin', { ssoId, tenantId });
    return ssoId;
  }

  // SAML 2.0 SSO Implementation
  async createSAMLSSO(tenantId: string, samlConfig: SAMLConfig): Promise<string> {
    const ssoId = `saml_${tenantId}_${Date.now()}`;

    const samlSSOConfig: SSOConfig = {
      provider: 'saml',
      clientId: samlConfig.entityId,
      clientSecret: '', // Not used in SAML
      metadataUrl: samlConfig.assertionConsumerServiceUrl,
      enabled: true,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Store SAML configuration separately
    await firestore.collection('saml_configs').doc(ssoId).set(samlConfig);
    await firestore.collection('sso_configs').doc(ssoId).set(samlSSOConfig);

    this.ssoConfigs.set(ssoId, samlSSOConfig);

    logAudit('saml_sso_created', 'admin', { ssoId, tenantId });
    return ssoId;
  }

  // Generate SSO Authorization URL
  async getAuthorizationUrl(ssoId: string, redirectUri: string): Promise<string> {
    const config = this.ssoConfigs.get(ssoId);
    if (!config || !config.enabled) {
      throw new Error('SSO configuration not found or disabled');
    }

    switch (config.provider) {
      case 'azure':
        return this.buildAzureAuthUrl(config, redirectUri);
      case 'okta':
        return this.buildOktaAuthUrl(config, redirectUri);
      case 'google':
        return this.buildGoogleAuthUrl(config, redirectUri);
      case 'saml':
        return this.buildSAMLAuthUrl(ssoId, redirectUri);
      default:
        throw new Error('Unsupported SSO provider');
    }
  }

  private buildAzureAuthUrl(config: SSOConfig, redirectUri: string): string {
    const baseUrl = `https://login.microsoftonline.com/${config.tenantId}`;
    const params = new URLSearchParams({
      client_id: config.clientId,
      response_type: 'code',
      redirect_uri: redirectUri,
      scope: 'openid profile email',
      response_mode: 'query'
    });
    return `${baseUrl}/oauth2/v2.0/authorize?${params}`;
  }

  private buildOktaAuthUrl(config: SSOConfig, redirectUri: string): string {
    const baseUrl = `https://${config.domain}.okta.com`;
    const params = new URLSearchParams({
      client_id: config.clientId,
      response_type: 'code',
      redirect_uri: redirectUri,
      scope: 'openid profile email',
      response_mode: 'query'
    });
    return `${baseUrl}/oauth2/v2.0/authorize?${params}`;
  }

  private buildGoogleAuthUrl(config: SSOConfig, redirectUri: string): string {
    const params = new URLSearchParams({
      client_id: config.clientId,
      response_type: 'code',
      redirect_uri: redirectUri,
      scope: 'openid profile email',
      response_mode: 'query'
    });
    return `https://accounts.google.com/oauth/authorize?${params}`;
  }

  private buildSAMLAuthUrl(ssoId: string, redirectUri: string): string {
    // For SAML, redirect to SP-initiated SSO
    return `/saml/login/${ssoId}?redirect_uri=${encodeURIComponent(redirectUri)}`;
  }

  // Process SSO Callback
  async processCallback(ssoId: string, code: string, redirectUri: string): Promise<any> {
    const config = this.ssoConfigs.get(ssoId);
    if (!config) {
      throw new Error('SSO configuration not found');
    }

    try {
      let userInfo: any;

      switch (config.provider) {
        case 'azure':
          userInfo = await this.processAzureCallback(config, code, redirectUri);
          break;
        case 'okta':
          userInfo = await this.processOktaCallback(config, code, redirectUri);
          break;
        case 'google':
          userInfo = await this.processAzureCallback(config, code, redirectUri); // Use Azure as fallback for Google
          break;
        case 'saml':
          userInfo = await this.processSAMLCallback(ssoId, code);
          break;
        default:
          throw new Error('Unsupported SSO provider');
      }

      logAudit('sso_callback_processed', 'system', { ssoId, provider: config.provider, email: userInfo.email });
      return userInfo;

    } catch (error) {
      logAudit('sso_callback_error', 'system', { ssoId, error: (error as Error).message });
      throw error;
    }
  }

  private async processAzureCallback(config: SSOConfig, code: string, redirectUri: string): Promise<any> {
    interface TokenResponse {
      id_token: string;
      access_token: string;
    }
    // Azure AD token exchange implementation
    const tokenUrl = `https://login.microsoftonline.com/${config.tenantId}/oauth2/v2.0/token`;

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri
      })
    });

    const tokens = await response.json() as any;

    // Decode ID token to get user info
    const userInfo = this.decodeJwt(tokens.id_token);
    return {
      id: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      provider: 'azure',
      ssoId: config.tenantId
    };
  }

  private async processOktaCallback(config: SSOConfig, code: string, redirectUri: string): Promise<any> {
    interface TokenResponse {
      id_token: string;
      access_token: string;
    }
    // Okta token exchange implementation
    const tokenUrl = `https://${config.domain}.okta.com/oauth2/v2.0/token`;

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri
      })
    });

    const tokens = await response.json() as TokenResponse;

    // Decode ID token to get user info
    const userInfo = this.decodeJwt(tokens.id_token);

    return {
      id: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      provider: 'google',
      ssoId: config.clientId
    };
  }

  private async processSAMLCallback(ssoId: string, samlResponse: string): Promise<any> {
    // SAML response processing (simplified)
    // In production, use a SAML library like saml2-js
    const decodedResponse = Buffer.from(samlResponse, 'base64').toString();

    // Parse SAML assertion (simplified parsing)
    const email = decodedResponse.match(/<saml:NameID[^>]*>([^<]+)</)?.[1];
    const name = decodedResponse.match(/<saml:Attribute[^>]*Name="displayName"[^>]*>.*?<saml:AttributeValue>([^<]+)</)?.[1];

    return {
      id: email, // Use email as ID for SAML
      email,
      name: name || email,
      provider: 'saml',
      ssoId
    };
  }

  private decodeJwt(token: string): any {
    const payload = token.split('.')[1];
    const decoded = Buffer.from(payload, 'base64').toString();
    return JSON.parse(decoded);
  }

  // Get SSO configurations for tenant
  async getTenantSSOConfigs(tenantId: string): Promise<SSOConfig[]> {
    const configs: SSOConfig[] = [];

    for (const [ssoId, config] of this.ssoConfigs.entries()) {
      if (ssoId.includes(tenantId)) {
        configs.push(config);
      }
    }

    return configs;
  }
}

// Initialize SSO service
export const ssoService = new SSOService();

// Initialize on startup
ssoService.initializeProviders().catch(console.error);

export { SSOService, type SSOConfig, type SAMLConfig };