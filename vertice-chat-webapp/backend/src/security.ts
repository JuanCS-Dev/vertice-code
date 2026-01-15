import express from 'express';
import cors from 'cors';
import { VertexAI } from '@google-cloud/vertexai';
import { Firestore } from '@google-cloud/firestore';
import Stripe from 'stripe';

// SOC 2 Security Controls Implementation
const securityHeaders = {
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Content-Security-Policy': "default-src 'self'",
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',

  // 🇪🇺 EU AI ACT COMPLIANCE HEADERS (MANDATORY 2026)
  'X-AI-Generated': 'true',
  'X-Model-Version': 'gemini-2.5-pro',
  'X-AI-Provider': 'Google Vertex AI',
  'X-Content-Provenance': 'vertice-ai-ledger-v1', // Simulates C2PA credential
  'X-Risk-Category': 'limited' // GPAI Transparency requirement
};

// Audit logging function (SOC 2 requirement)
function logAudit(event: string, userId: string, details: any) {
  const auditEntry = {
    timestamp: new Date().toISOString(),
    event,
    userId,
    ip: '', // Would be populated from request
    userAgent: '', // Would be populated from request
    details,
    compliance: 'soc2_type2'
  };

  console.log('AUDIT:', JSON.stringify(auditEntry));
  // In production, send to Cloud Logging or SIEM
}

// Rate limiting (SOC 2 availability control)
const rateLimit = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 1000; // requests per hour
const RATE_WINDOW = 60 * 60 * 1000; // 1 hour

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const userLimit = rateLimit.get(ip);

  if (!userLimit || now > userLimit.resetTime) {
    rateLimit.set(ip, { count: 1, resetTime: now + RATE_WINDOW });
    return true;
  }

  if (userLimit.count >= RATE_LIMIT) {
    logAudit('rate_limit_exceeded', 'system', { ip, count: userLimit.count });
    return false;
  }

  userLimit.count++;
  return true;
}

// Input validation (SOC 2 processing integrity)
function validateInput(data: any, schema: Record<string, any>): boolean {
  // Basic validation - in production use Zod or similar
  if (!data || typeof data !== 'object') return false;

  for (const [key, rules] of Object.entries(schema)) {
    if (rules.required && !data[key]) return false;
    if (rules.type && typeof data[key] !== rules.type) return false;
    if (rules.maxLength && typeof data[key] === 'string' && data[key].length > rules.maxLength) return false;
  }

  return true;
}

// SOC 2 Access Control Middleware
function requireAuth(req: express.Request, res: express.Response, next: express.NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    logAudit('unauthorized_access', 'unknown', { path: req.path, ip: req.ip });
    return res.status(401).json({ error: 'Authentication required' });
  }

  // In production: validate JWT token with Firebase Auth
  const token = authHeader.substring(7);
  if (!token) {
    return res.status(401).json({ error: 'Invalid token' });
  }

  // Rate limiting check
  if (!checkRateLimit(req.ip || 'unknown')) {
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  logAudit('successful_auth', 'user_id_here', { path: req.path });
  next();
}

// SOC 2 - Encryption at Rest Implementation
class EncryptionService {
  private algorithm = 'aes-256-gcm';
  private keyLength = 32; // 256 bits

  async encryptData(data: string, key?: string): Promise<string> {
    // In production: use proper KMS or envelope encryption
    // This is a simplified implementation for demonstration
    const crypto = await import('crypto');
    const encryptionKey = key || process.env.ENCRYPTION_KEY || 'default-key-change-in-production';

    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.algorithm, encryptionKey);

    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    return `${iv.toString('hex')}:${encrypted}`;
  }

  async decryptData(encryptedData: string, key?: string): Promise<string> {
    const crypto = await import('crypto');
    const encryptionKey = key || process.env.ENCRYPTION_KEY || 'default-key-change-in-production';

    const [ivHex, encrypted] = encryptedData.split(':');
    const iv = Buffer.from(ivHex, 'hex');

    const decipher = crypto.createDecipher(this.algorithm, encryptionKey);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// SOC 2 - Backup & Recovery Procedures
class BackupService {
  async createBackup(tenantId: string, data: any): Promise<string> {
    const backupId = `backup_${tenantId}_${Date.now()}`;
    const backupData = {
      id: backupId,
      tenantId,
      timestamp: new Date().toISOString(),
      data: await new EncryptionService().encryptData(JSON.stringify(data)),
      checksum: this.generateChecksum(data)
    };

    // In production: store in secure backup location
    logAudit('backup_created', 'system', { backupId, tenantId });
    return backupId;
  }

  async restoreBackup(backupId: string): Promise<any> {
    // In production: retrieve from secure backup location
    logAudit('backup_restored', 'system', { backupId });
    return {}; // Placeholder
  }

  private generateChecksum(data: any): string {
    // Generate SHA-256 checksum for integrity verification
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
  }
}

// SOC 2 - Change Management
class ChangeManagementService {
  async submitChangeRequest(change: ChangeRequest): Promise<string> {
    const changeId = `change_${Date.now()}`;
    const changeRequest = {
      id: changeId,
      ...change,
      status: 'pending',
      submittedAt: new Date().toISOString(),
      approvedBy: null,
      implementedAt: null
    };

    // In production: store in change management database
    logAudit('change_request_submitted', change.submittedBy, { changeId, type: change.type });
    return changeId;
  }

  async approveChange(changeId: string, approver: string): Promise<void> {
    // In production: update change status and implement change
    logAudit('change_request_approved', approver, { changeId });
  }
}

interface ChangeRequest {
  title: string;
  description: string;
  type: 'code' | 'infrastructure' | 'security' | 'data';
  impact: 'low' | 'medium' | 'high' | 'critical';
  submittedBy: string;
  plannedImplementation: string;
  rollbackPlan: string;
}

// SOC 2 - Incident Response
class IncidentResponseService {
  async reportIncident(incident: IncidentReport): Promise<string> {
    const incidentId = `incident_${Date.now()}`;
    const incidentReport = {
      id: incidentId,
      ...incident,
      status: 'reported',
      reportedAt: new Date().toISOString(),
      resolvedAt: null,
      resolution: null
    };

    // Alert security team immediately
    await this.alertSecurityTeam(incidentReport);

    logAudit('incident_reported', incident.reportedBy, {
      incidentId,
      severity: incident.severity,
      type: incident.type
    });

    return incidentId;
  }

  async resolveIncident(incidentId: string, resolution: string, resolver: string): Promise<void> {
    logAudit('incident_resolved', resolver, { incidentId, resolution });
  }

  private async alertSecurityTeam(incident: any): Promise<void> {
    // In production: send alerts via email, Slack, PagerDuty, etc.
    console.error('🚨 SECURITY INCIDENT ALERT:', JSON.stringify(incident, null, 2));
  }
}

interface IncidentReport {
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: 'security' | 'availability' | 'data_breach' | 'compliance';
  affectedSystems: string[];
  reportedBy: string;
  evidence: any;
}

// SOC 2 - Access Review Procedures
class AccessReviewService {
  async scheduleAccessReview(tenantId: string): Promise<string> {
    const reviewId = `access_review_${tenantId}_${Date.now()}`;
    const reviewSchedule = {
      id: reviewId,
      tenantId,
      scheduledDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
      status: 'scheduled',
      reviewers: [],
      findings: []
    };

    logAudit('access_review_scheduled', 'system', { reviewId, tenantId });
    return reviewId;
  }

  async conductAccessReview(reviewId: string, reviewer: string, findings: AccessFinding[]): Promise<void> {
    logAudit('access_review_completed', reviewer, { reviewId, findingsCount: findings.length });
  }
}

interface AccessFinding {
  userId: string;
  resource: string;
  issue: string;
  severity: 'low' | 'medium' | 'high';
  recommendation: string;
}

// SOC 2 - Monitoring & Alerting
class MonitoringService {
  private alerts: AlertRule[] = [
    {
      name: 'High Error Rate',
      condition: (metrics) => metrics.errorRate > 0.05, // 5%
      severity: 'high',
      action: (metrics) => this.alertHighErrorRate(metrics)
    },
    {
      name: 'Security Anomaly',
      condition: (metrics) => metrics.failedLogins > 10,
      severity: 'critical',
      action: (metrics) => this.alertSecurityAnomaly(metrics)
    },
    {
      name: 'Data Exfiltration',
      condition: (metrics) => metrics.unusualDataAccess > 1000,
      severity: 'critical',
      action: (metrics) => this.alertDataExfiltration(metrics)
    }
  ];

  async checkMetrics(metrics: SystemMetrics): Promise<void> {
    for (const alert of this.alerts) {
      if (alert.condition(metrics)) {
        await alert.action(metrics);
        logAudit('alert_triggered', 'system', {
          alertName: alert.name,
          severity: alert.severity,
          metrics
        });
      }
    }
  }

  private async alertHighErrorRate(metrics: SystemMetrics): Promise<void> {
    console.error('🚨 HIGH ERROR RATE ALERT:', metrics);
    // In production: send to monitoring system
  }

  private async alertSecurityAnomaly(metrics: SystemMetrics): Promise<void> {
    console.error('🚨 SECURITY ANOMALY ALERT:', metrics);
    await new IncidentResponseService().reportIncident({
      title: 'Security Anomaly Detected',
      description: `${metrics.failedLogins} failed login attempts detected`,
      severity: 'high',
      type: 'security',
      affectedSystems: ['authentication'],
      reportedBy: 'system',
      evidence: metrics
    });
  }

  private async alertDataExfiltration(metrics: SystemMetrics): Promise<void> {
    console.error('🚨 DATA EXFILTRATION ALERT:', metrics);
    await new IncidentResponseService().reportIncident({
      title: 'Potential Data Exfiltration',
      description: `${metrics.unusualDataAccess} unusual data access events`,
      severity: 'critical',
      type: 'data_breach',
      affectedSystems: ['database'],
      reportedBy: 'system',
      evidence: metrics
    });
  }
}

interface AlertRule {
  name: string;
  condition: (metrics: SystemMetrics) => boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
  action: (metrics: SystemMetrics) => Promise<void>;
}

interface SystemMetrics {
  errorRate: number;
  failedLogins: number;
  unusualDataAccess: number;
  responseTime: number;
  uptime: number;
  activeUsers: number;
}

// SOC 2 - Configuration Management
class ConfigurationManagementService {
  private configChanges: ConfigChange[] = [];

  async recordConfigChange(change: ConfigChange): Promise<void> {
    change.id = `config_${Date.now()}`;
    change.timestamp = new Date().toISOString();
    change.status = 'pending';

    this.configChanges.push(change);

    await new ChangeManagementService().submitChangeRequest({
      title: `Configuration Change: ${change.component}`,
      description: change.description,
      type: 'infrastructure',
      impact: change.impact,
      submittedBy: change.changedBy,
      plannedImplementation: change.timestamp,
      rollbackPlan: change.rollbackPlan
    });

    logAudit('config_change_recorded', change.changedBy, {
      changeId: change.id,
      component: change.component
    });
  }

  async validateConfiguration(component: string): Promise<boolean> {
    // In production: validate against security policies
    logAudit('config_validation_performed', 'system', { component });
    return true; // Placeholder
  }
}

interface ConfigChange {
  id?: string;
  component: string;
  property: string;
  oldValue: any;
  newValue: any;
  description: string;
  changedBy: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  timestamp?: string;
  status?: string;
  rollbackPlan: string;
}

// Initialize SOC 2 services
export const encryptionService = new EncryptionService();
export const backupService = new BackupService();
export const changeManagementService = new ChangeManagementService();
export const incidentResponseService = new IncidentResponseService();
export const accessReviewService = new AccessReviewService();
export const monitoringService = new MonitoringService();
export const configManagementService = new ConfigurationManagementService();

export {
  securityHeaders,
  logAudit,
  checkRateLimit,
  validateInput,
  requireAuth,
  EncryptionService,
  BackupService,
  ChangeManagementService,
  IncidentResponseService,
  AccessReviewService,
  MonitoringService,
  ConfigurationManagementService,
  type SystemMetrics,
  type IncidentReport,
  type ChangeRequest,
  type AccessFinding,
  type ConfigChange
};